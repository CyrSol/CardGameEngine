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
				self.board.stock.showFront().hidden = False
				self.board.fillDeck(52)

				self.state = Game.ACTION
				self.awaitEveryActive()
				self.changed=True
			

			elif self.state == Game.ACTION and len(self.awaited) == 0:
				if self.selected_target_deck.deckType == Deck.PLAYER :
					card_played = None
					if self.selected_deck.deckType == Deck.STOCK or self.selected_deck.deckType == Deck.BOARD:
						print(self.selected_deck.name)
						card_played = self.selected_deck.showFront()
						card_played.hidden = False
						card_played.marked = False
						if (self.mode == 0):
							card = self.selected_target_deck.selected[0]
							index = self.selected_target_deck.cards.index(card)
							self.selected_target_deck.cards[index] = card_played
						else:
							self.selected_target_deck.addFront(card_played)
						self.selected_deck.cards.remove(card_played)
						self.selected_deck.showFront().marked = True
						self.selected_deck.showFront().hidden = False
					else:
						for c in self.selected_deck.selected :
							self.selected_target_deck.addFront(c)
							self.selected_deck.cards.remove(c)

				elif self.selected_target_deck.deckType != Deck.PLAYER :
					for c in self.selected_deck.selected :
						c.marked = False
						self.board.discard(c)
						self.selected_deck.cards.remove(c)

				self.selected_target_deck.selected = []
				self.selected_deck.selected = []
				if self.selected_deck.deckType == Deck.PLAYER :
					self.selected_target_deck = None
					self.selected_deck = None
					self.mode = 0
				self.awaitEveryActive()
				self.changed=True


			

	def game_action(self, message,player,deck,card):
		
		if(not  self.isGameOver()):
			
			if(player.name in self.awaited and deck != None):
				
				if  self.selected_deck != None and  self.selected_target_deck != None and self.selected_deck != deck and self.selected_target_deck != deck:
					self.selected_deck.showFront().marked = False
					self.selected_deck = None
					self.selected_target_deck = None
					self.mode = 0
					self.changed = True
					return
				
				if (deck.deckType== Deck.STOCK or deck.deckType == Deck.BOARD or deck.deckType== Deck.WASTE) :
					if((self.selected_deck == None or self.selected_deck.deckType != Deck.PLAYER) and (deck.deckType== Deck.STOCK or deck.deckType == Deck.BOARD)) :
						if(self.selected_deck == deck):
							self.mode = (self.mode+1) % 2
						else :
							self.selected_deck = deck
							self.selected_deck.showFront().marked = True
						mode = "INSERT" if self.mode == 1 else "REPLACE"
						self.sendMessage(Message(Message.DEBUG,0,"game","Mode : " + mode))

					elif self.selected_deck != None:
						self.selected_target_deck = deck
						self.awaited.remove(player.name)
					self.changed = True
					
				elif (deck.deckType == Deck.PLAYER and self.selected_deck == None) :
					self.selected_deck = deck
					card.marked = True
					deck.selected.append(card)
					self.changed = True
				
				elif (deck.deckType == Deck.PLAYER and self.selected_deck == deck ) :
					if (card.marked) :
						card.marked = False
						deck.selected.remove(card)
						if (deck.selected == []):
							self.selected_deck = None
					else :
						card.marked = True
						deck.selected.append(card)
					self.changed = True

				elif (deck.deckType== Deck.PLAYER and self.selected_deck != deck  and self.selected_deck != None ) :
					deck.selected.append(card)
					self.selected_target_deck = deck
					self.awaited.remove(player.name)
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
				if l.name == "waste":
					type = Deck.WASTE
				if l.name == "stock":
					type = Deck.STOCK
				deck = Deck(l.name,type)
				self.decks.append(deck)
				deck.addBack(emptyCard())
				self.interfacedDecks.append(InterfacedDeckDescriptor(deck,Deck.PLAYER))
		self.interfacedDecks.append(InterfacedDeckDescriptor(self.board.deck,Deck.STOCK))
		self.interfacedDecks.append(InterfacedDeckDescriptor(self.board.stock,Deck.STOCK))
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

