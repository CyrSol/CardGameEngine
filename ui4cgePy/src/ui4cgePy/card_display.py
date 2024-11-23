import pygame
import sys
import os
import datetime
from cgePy.card_manager import *

from ui4cgePy.GameWindowTK import *


#Define sizes
#-----------------------
SCREEN_WIDTH=790
SCREEN_HEIGHT=540
STOCK_X=210
STOCK_Y=10
WASTE_X=300
WASTE_Y=30
STOCK_MARGE=0
WASTE_MARGE=0
FONT_SIZE=25
CARD_WIDTH = 120
CARD_HEIGHT = int(CARD_WIDTH*1.3)
#-----------------------


class GameDISP(Game):
	
	def __init__(self,general_params,game_params):
		Game.__init__(self,general_params,game_params)
		self.awaited = []
		self.decksTab = []
		for i in range(0,3):
			deck = Deck("Deck" + str(i))
			self.decksTab.append(deck)
			self.decks.append(deck)
		self.stack = []
		self.player=0
		self.rules = []
		self.rules_combo = []
		self.global_rules= []
		#self.tab = [[None,None,None],[None,None,None],[None,None,None]]


	def start(self):
		self.state = Game.DISTRIBUTION
		self.gameInitialisation()

	
	def step(self):
		self.changed=True
		if(not self.isGameOver()):
			if self.state == Game.DISTRIBUTION:
				self.game_count=self.game_count+1
				for p in self.players :
					p.cards=[]

				self.board.fillStock()
				for c in self.board.stock.cards:
					c.hidden = False
				
				for pl in self.players:
					pl.current_score = 0

				
				self.state = Game.SELECTION
				self.awaited.append(self.players[0].name)
				self.changed=True
				
			elif self.state == Game.ACTION:
				
				card = self.board.stock.selected[0]
				card.marked = False
				self.board.stock.selected = []
				self.board.discard(self.board.draw())
				if(self.board.stock.isEmpty()):
					self.state = Game.DISTRIBUTION
				else:
					self.state = Game.SELECTION
					self.awaited.append(self.players[0].name)				
				self.changed=True
					
			

	def game_action(self, message,player,deck,card):
		
		if(not  self.isGameOver()):
			if(player.name in self.awaited):
				
					
				if (message.messageType == Deck.STOCK) and self.state == Game.SELECTION :
					#card.hidden = not card.hidden	
					if not card.marked:
						card.marked = True 
						self.board.stock.selected = [card]
						sendMessagePlayer(player, "Vous avez selectionné la carte : " + card.getInfo())
					else:
						self.state = Game.ACTION
						self.awaited.remove(player.name)
						sendMessagePlayer(player, "Vous avez joué la carte : " + card.getInfo())
					self.changed=True

				if (message.messageType == Deck.WASTE) and self.state == Game.SELECTION :
					#card.hidden = not card.hidden	
					card.marked = not card.marked
					self.changed=True

	def loadInterfacedDecks(self):
		self.interfacedDecks.append(InterfacedDeckDescriptor(self.board.stock, self.board.stock.deckType))
		self.interfacedDecks.append(InterfacedDeckDescriptor(self.board.waste, self.board.waste.deckType))
	

class GameFactoryDISP(GameFactory):
	
	def getGame(self):
		return GameDISP(self.general_params,self.game_params)

class AIFactoryDISP():
	def getAI(self,num):
		return AI("rien",0) if num != 0 else None

def debug_display_cards(general_params,loadCards):	
	game_params=loadParams(general_params["game_params"])

	gameSceneFactoryList=[]
	gameSceneFactoryList.append(GameLogicFactory(GameManagerFactory(GameFactoryDISP(general_params,game_params),AIFactoryDISP(),loadCards)))

	GameWindowTK.display(general_params,game_params,gameSceneFactoryList,SimpleTransitionManager())

