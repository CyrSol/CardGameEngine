import pygame
import sys
import os
import datetime

from cgePy.card_game import *
from cgePy.card_manager import GameFactory
from ui4cgePy.card_display import *


class GameUTRC(Game):
	
	def __init__(self,general_params,game_params):
		Game.__init__(self,general_params,game_params)
		self.awaited = []
		self.nbCards=0
		self.selected_deck = None
		self.selected_target_deck = None
		self.mode = 0
		self.actionDeck = None

	def start(self):
		self.state = Game.INITIALISATION
		self.gameInitialisation()
	
	def step(self):
		if(not self.isGameOver()):

			if self.state == Game.INITIALISATION:
				self.state = Game.DISTRIBUTION
				self.active_players_index =[0]
				self.changed=True		

			if self.state == Game.DISTRIBUTION:

				self.board.fillStock()
				#self.board.stock.showFront().hidden = False
				self.board.fillDeck(52)

				self.state = Game.ACTION
				self.awaitEveryActive()
				self.changed=True
			

			elif self.state == Game.ACTION and len(self.awaited) == 0:
				
				card_played = None
				b = len(self.selected_target_deck.selected) > 0 and not self.selected_target_deck.selected[0] == None and self.selected_target_deck.selected[0].name == ""
				if (b):
					self.selected_target_deck.cards.remove(self.selected_target_deck.selected[0])
				for c in self.selected_deck.selected :
					if self.mode == 0 :
						self.selected_target_deck.addFront(c)
					else:
						self.selected_target_deck.addBack(c)
					self.selected_deck.cards.remove(c)
					c.marked = False



				self.selected_target_deck.selected = []
				self.selected_deck.selected = []
				self.selected_target_deck = None
				self.selected_deck = None
				self.mode = 0
				self.awaitEveryActive()
				self.changed=True


			

	def game_action(self, message,player,deck,card):
		
		if(not  self.isGameOver()):

			if isinstance(message,MessageValue) and  "button_g" in message.value[0] and self.selected_deck is not None:
				if message.value[0] == "button_g":
					list_choice = ["shuffle","face up","face down","select all","unselect"]
					options_dic = addOption({},"action_choice","string",list_choice,"choose an action")
					dic = dicOptionsMaker("UTRC",options_dic)
					self.addOutputMessage(MessageValue( Message.CHOICE,Deck.CHOICE, self.players[0].name, "output", dic))
				self.state = Game.SELECTION
				return

			if isinstance(message,MessageValue) and  "button_h" in message.value[0] and self.selected_deck is not None:
				if message.value[0] == "button_h":
					list_choice = []
					for i in range (0,self.selected_deck.getNbCards()+1):
						list_choice.append(i)
					options_dic = addOption({},"action_choice","integer",list_choice,"chose the number of cards to select")
					dic = dicOptionsMaker("UTRC",options_dic)
					self.addOutputMessage(MessageValue( Message.CHOICE,Deck.CHOICE, self.players[0].name, "output", dic))
				self.state = Game.AUCTION
				return

			if(self.state == Game.SELECTION and self.selected_deck is not None):
				self.actionDeck = message.value[0]
				if self.actionDeck == "shuffle":
					self.selected_deck.shuffle()
					if len(self.selected_deck.selected) > 0:
						for c in self.selected_deck.selected:
							c.marked = False
						self.selected_deck.selected = []
				elif self.actionDeck == "face up":
					if not self.selected_deck.isEmpty():
						for c in self.selected_deck.cards:
							c.hidden = False
				elif self.actionDeck == "face down":
					if not self.selected_deck.isEmpty():
						for c in self.selected_deck.cards:
							c.hidden = True
				elif self.actionDeck == "select all":
					if not self.selected_deck.isEmpty():
						for c in self.selected_deck.cards:
							if c.marked == False:
								c.marked = True
								self.selected_deck.selected.append(c)
				elif self.actionDeck == "unselect":
					if not self.selected_deck.isEmpty():
						for c in self.selected_deck.cards:
							if c.marked == True:
								c.marked = False
							if self.selected_deck  is not None :
								self.selected_deck.selected = []
								self.selected_deck = None
				self.actionDeck = None
				self.state = Game.ACTION
				self.changed = True
				return

			if(self.state == Game.AUCTION and self.selected_deck is not None):
				nbCards = int(message.value[0])
				if nbCards > 0 :
					for c in self.selected_deck.selected :
						c.marked = False
					self.selected_deck.selected =  []
					for i in range(0,nbCards):
						self.selected_deck.selected.append(self.selected_deck.cards[i])
						self.selected_deck.cards[i].marked = True
					self.changed = True
				self.state = Game.ACTION
				
				return


			if(player.name in self.awaited and deck != None):
				
				if  self.selected_deck != None and  self.selected_target_deck != None and self.selected_deck != deck and self.selected_target_deck != deck:
					self.selected_deck.showFront().marked = False
					self.selected_deck = None
					self.selected_target_deck = None
					self.mode = 0
					self.changed = True
					return
				
					
				elif ((deck.deckType == Deck.PLAYER or deck.deckType== Deck.STOCK or deck.deckType == Deck.BOARD or deck.deckType== Deck.WASTE) and self.selected_deck == None) :
					if card is not None :
						self.selected_deck = deck
						card.marked = True
						deck.selected.append(card)
						self.changed = True
				
				elif ((deck.deckType == Deck.PLAYER or deck.deckType== Deck.STOCK or deck.deckType == Deck.BOARD or deck.deckType== Deck.WASTE) and self.selected_deck == deck ) :
					if (card.marked) :
						if((not card.hidden and message.messageType != Deck.SORT) or (card.hidden and message.messageType == Deck.SORT)  ) :
							card.marked = False
							deck.selected.remove(card)
							if (deck.selected == []):
								self.selected_deck = None
						else :
							card.hidden = message.messageType == Deck.SORT
					else :
						card.marked = True
						deck.selected.append(card)
					self.changed = True

				elif ((deck.deckType == Deck.PLAYER or deck.deckType== Deck.STOCK or deck.deckType == Deck.BOARD or deck.deckType== Deck.WASTE)  and self.selected_deck != deck  and self.selected_deck != None ) :
					deck.selected.append(card)
					self.selected_target_deck = deck
					self.awaited.remove(player.name)
					if message.messageType == Deck.SORT:
						self.mode = 1
					self.changed = True



	def loadInterfacedDecks(self):
		basePath = os.getcwd()
		cpl = ""
		if self.general_params["multi_fic_config"]:
			cpl = str(self.game_params["nb_players"])
		ccfgPath = os.path.join(self.general_params["fic_config_folder"] + self.general_params["fic"]+cpl+self.general_params["extension_fic_config"])
		fic = open(ccfgPath,'r')
		interfaceLines =interfaceLineFromFile(fic)
		
		self.board.deck.name = "deck_ut"
		self.board.stock.name = "stock_ut"
		self.board.waste.name = "waste_ut"
		for l in interfaceLines :
			if l.name not in ["deck_ut","stock_ut","waste_ut"] :
				type = Deck.PLAYER
				if l.name == "PLAYER":
					type = Deck.WASTE
				if l.name == "PLAYER":
					type = Deck.STOCK
				deck = Deck(l.name,type)
				self.decks.append(deck)
				deck.addBack(emptyCard())
				self.interfacedDecks.append(InterfacedDeckDescriptor(deck,Deck.PLAYER))
		self.interfacedDecks.append(InterfacedDeckDescriptor(self.board.deck,Deck.STOCK))
		self.interfacedDecks.append(InterfacedDeckDescriptor(self.board.stock,Deck.PLAYER))
		self.interfacedDecks.append(InterfacedDeckDescriptor(self.board.waste,Deck.WASTE))

		

		
class GameFactoryUTRC(GameFactory):
	
	def getGame(self):
		return GameUTRC(self.general_params,self.game_params)

class AIUTRCFactory():
	def getAI(self,num):
		return None

def record_unit_tests(general_params,aIFactory,loadCards=loadCards):
	
	game_params=loadParams(general_params["game_params"])
	game_options=loadParams(general_params["game_options"])


	
	gameSceneFactoryList=[]
	gameSceneFactoryList.append(GameLogicFactory(GameManagerFactory(GameFactoryUTRC(general_params,game_params),aIFactory,loadCards)))
	GameWindowTK.display(general_params,game_params,gameSceneFactoryList,SimpleTransitionManager(),game_options)

