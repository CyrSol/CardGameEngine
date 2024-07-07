import random
import copy
import json, os, sys
import datetime
sys.path.append("..")
from cards.card_stats import *


class Card(object):
	""" card's attribut"""
	
	def __init__(self,name,rank,suit,value,tag):
		self.name=name
		self.rank=rank
		self.suit=suit
		self.tag=tag
		self.value=value
		self.hidden=True
		self.marked=False
		self.fixed=False
		self.handle=False
		#self.points= points

	def getInfo(self):
		return self.name
	
	def getValue(self):
		return self.suit + self.name

	def getSymbol(self):
		return self.suit, int(self.rank)

def getCardValueSort(card):
	return card.getValue()

def getCardSymbol(index,card):
	return index, card.getSymbol()

def getDeckSymbol(deck):
	result=[]
	for card in deck.cards:
		result.append(getCardSymbol(deck.cards.index(card), card))
	return result

def getDeckSymbolMax(deckSymbol):
	if (len(deckSymbol) >= 0):
		i,(s,mini) = deckSymbol[0]

		for i,(s,r)  in deckSymbol :
			if r < mini:
				mini = r

		return [(i,(s,r)) for (i,(s,r)) in deckSymbol if r == mini][0]

def getDeckSymbolMin(deckSymbol):
	if (len(deckSymbol) >= 0):
		i,(s,maxi) = deckSymbol[0]

		for i,(s,r) in deckSymbol :
			if r > maxi:
				maxi = r

		return [(i,(s,r)) for (i,(s,r)) in deckSymbol if r == maxi][0]

class Deck(object) :
	STOCK = 0
	WASTE = 1
	PLAYER = 2
	SELECTED = 3
	BOARD = 4
	CHOICE= 5
	SORT = 6
	

	def __init__(self,name,deckType = 4):
		self.cards = []
		self.name=name
		self.selected = []
		self.handled = []
		self.tag= ""
		self.deckType = deckType
		self.cardsOwned = {}
		self.cardsPlayable = []
		

	def shuffle(self):
		r=[]
		length = len(self.cards)
		for i in range(length):
			if len(self.cards) > 1:
				c = random.choice(self.cards)
				r.append(c)
				self.cards.remove(c)
			else:
				c = self.cards.pop()
				r.append(c)
		self.cards = r
		
	def addFront(self,card):
		self.cards.insert(0,card)
	
	def addBack(self,card):
		self.cards.append(card)
	
	def getFront(self):
		if not self.isEmpty():
			return self.cards.pop(0)
	
	def getBack(self):
		if not self.isEmpty():
			return self.cards.pop()

	def isEmpty(self):
		return len(self.cards) == 0
	
	def showFront(self):
		if(not self.isEmpty()):
			return self.cards[0]
	
	def getSelected(self):
		#return [card for card in self.cards if card.marked == True]
		return self.selected
	
	def removeCard(self,card):
		self.cards.remove(card)
	
	def getNbCards(self):
		return len(self.cards)

	def sort(self,reverse=False):
		self.cards.sort(key = getCardValueSort, reverse = reverse)  

	def getValue(self):
		return sum(map(lambda x: x.value, self.cards))

class Player(Deck) :
	
	def __init__(self,name):
		Deck.__init__(self,name,Deck.PLAYER)
		self.selectedCards = []
		self.current_score=0
		self.auction = 0
		self.score=0
		self.victory = 0
		self.stats=[]
		self.nature='humain'
		self.messages=[]
		self.round_won=0
	
		
	def selectCard(self,card):
		if(cards in self.cards):
			self.selectedCards.append(card)
	
	def unselectCards(self):
		self.selectedCards = []

	def sendMessage(self,message):
		self.messages.append(message)

class PlayerAI(Player):

	def __init__(self,name,ai):
		Player.__init__(self,name)
		self.ai=ai
		self.nature = ai.nature

	def play(self,game):
		return self.ai.play(game,self)
		
class AI(object):
	def __init__(self,level,nature):
		self.level=level
		self.nature= nature

	def play(self,game,player):
		return MessageDeck(Message.GAME,Deck.STOCK,player.name,"stock",0)

class AIManager(object):
		def __init__(self):
			self.players=[]
		
		def play(self,game):
			messages=[]
			for p in self.players:
				if p.name in game.awaited:
					message = p.play(game)
					if message is not None:
						messages.append(message)
			return messages
					
		def addPlayer(self,player):
			self.players.append(player)

		def getNbPlayers(self):
			return len(self.players)

class Board(object) :
	
	def __init__(self):
		self.stock = Deck("stock",Deck.STOCK)
		self.waste = Deck("waste",Deck.WASTE)
		self.stock_init = Deck("stock_init",Deck.STOCK)
		self.info = ""
		self.cards_ref = {}
	
	def initialisation(self,cards, cards_ref):
		self.stock_init.cards = cards
		self.cards_ref = cards_ref

	def fillStock(self):
		self.stock.cards = []
		for c in self.stock_init.cards:
			self.stock.cards.append(copy.deepcopy(c))

	def getCardFromName(self,cardName):
		return copy.deepcopy(self.cards_ref[cardName])
		
	def getCompl(self):
		return self.cards_ref

	def shuffle(self):
		self.stock.shuffle()
		
	def emptyWaste(self) :
		self.waste.cards = []
		
	def draw(self):
		return self.stock.getFront()
	
	def discard(self, card):
		self.waste.addFront(card)
	
	def isStockEmpty(self):
		return self.stock.isEmpty()
		
	def showStock(self):
		if(not self.stock.isEmpty()):
			return self.stock.cards[0]
	
	def showWaste(self):
		if(not self.waste.isEmpty()):
			return self.waste.cards[0]
	
	def setInfo(self, str):
		self.info = str
	
	
class Message():
	DEBUG=0
	INFO=1
	GAME=2
	CHOICE=3

	def __init__(self, level, messageType, playerName, text):
		self.level= level
		self.messageType = messageType
		self.playerName=playerName
		self.text = text

	def to_string(self):
		return self.text


class MessageDeck(Message):
	
	def __init__(self, level,messageType, playerName,  deckName, index):
		text = "De : " + playerName + " vers :"+ deckName + " type:" +  str(messageType) + "/i" +  str(index)
		Message.__init__(self,level,messageType,playerName, text)
		self.deckName=deckName
		self.index=index

class MessageValue(Message):
	
	def __init__(self, level,messageType, playerName, text, value):
		Message.__init__(self,level,messageType,playerName,text)
		self.value=value

class InterfacedDeckDescriptor:
	def __init__(self, interfacedDeck):
		self.deck = interfacedDeck
		self.deckType = interfacedDeck.deckType

	def __init__(self, interfacedDeck, deckType):
		self.deck = interfacedDeck
		self.deckType = deckType

class UIElementDescriptor:
	def __init__(self, interfacedDeck):
		self.deck = interfacedDeck

		self.deckType = interfacedDeck.deckType

	def __init__(self, interfacedDeck, deckType):
		self.deck = interfacedDeck
		self.deckType = deckType

class Game(object) :
	GAME_OVER = 0
	REINIT_PLAYER=15
	DISTRIBUTION = 1
	SELECTION = 2
	CONFIRMATION = 3
	ACTION = 4
	EXPECTATION = 5
	VALIDATION= 6
	PROPAGATION=7
	INITIALISATION=8
	END_DISTIBUTION=9
	AUCTION=10
	PRE_ACTION=11
	REFLECTION=12
	REACTION=13
	PREPARATION=14

	def __init__(self,general_params,game_params):
		self.board = Board()
		self.players = []
		self.messages = []
		self.decks = []
		self.decks.append(self.board.stock)
		self.decks.append(self.board.waste)
		#self.game_over = False
		self.changed = False
		self.state=0
		self.awaited=[]
		self.round_count=0
		self.game_count=0
		self.nb_games=-1
		self.fullAI= False
		self.interfacedDecks = []
		self.selected = Deck("selected",Deck.SELECTED)
		self.debug = ""
		self.game_params = {}
		self.general_params=general_params
		self.game_params = game_params
		self.output_messages=[]
		self.nameFicStats=""
		#self.loadGameParams()
		self.uiVars= {}
		self.rules =[]
		

	def start(self):
		print("GO!")
	
	def step(self):
		print("Step!")
		
	def cleanMessages(self):
		self.messages = []

	def cleanOutputMessages(self):
		self.output_messages = []

	def gameInitialisation(self):
		self.round_count=0
		#self.game_count=self.game_count+1
		for pl in self.players:
			pl.stats.append(Stats())
			pl.current_score=0
			pl.score=0
			pl.auction=0
		self.nameFicStats = self.general_params["log_file"]  + "_" + str(datetime.datetime.now()) + ".csv"
		self.nb_games = self.game_params["nb_games"]

	def addPlayer(self,player):
		self.players.append(player)
		self.decks.append(player)
	
	def sendMessage(self,message):
		self.messages.append(message)
		
	def addOutputMessage(self,message):
		self.output_messages.append(message)

	def getPlayer(self,name):
		for p in self.players:
			if name == p.name:
				return p
	def getNbPlayers(self):
		return len(self.players)
	
	def getDeck(self,name):
		for d in self.decks :
				if d.name == name:
					return d
	def readMessages(self):
		for message in self.messages : 
			if message is not None :
				player = self.getPlayer(message.playerName)
				#print(player.name)
				deck=None
				if not message.messageType == Deck.SELECTED and not message.messageType == Deck.CHOICE:
					deck = self.getDeck(message.deckName)
				if deck is not None and message.index >= 0 and deck.getNbCards() > 0:
					card = deck.cards[message.index]
				else: card = None
				#print(message.to_string())
				if card is not None:
					self.debug = card.getInfo()
				self.action(message,player,deck,card)
		self.cleanMessages()
		
	def action(self, message,player,deck,card):
		message.playerName
		for c in player.handled:
			if c not in player.cards :
				c.handle = False
				player.handled.remove(c)
				
		#print (message.playerName + " -> " + message.deckName+ " -> " + str(message.index))
		if (message.messageType == Deck.SORT) and player == deck :
			#print(card.getInfo())
			if card in player.handled or len(player.handled) == 0 :
				card.handle=not card.handle
				if card.handle:
					player.handled.append(card)
				else:
					player.handled.remove(card)
			else:
				card2 = player.handled[0]
				if card2 in player.cards :
					ind1 = player.cards.index(card)
					ind2 =player.cards.index(card2)
					player.cards.remove(card2)
					player.cards.insert(ind1,card2)
					#player.cards.remove(card)
					#player.cards.insert(ind2,card)
				card2.handle= False
				player.handled = []
			self.changed=True
	
	def isGameOver(self):
		return self.state == Game.GAME_OVER

	def saveGameParams(self):
		saveParams(self.general_params["game_params"],self.game_params)
		self.debug = "Paramètres de jeu sauvegardés"

	def loadGameParams(self):
		self.game_params = loadParams(self.general_params["game_params"])

	def saveStats(self):
		if self.game_params["benchmarkAI"] == 0:
			printStats(self.nameFicStats,self.players,StatsAggFactory())

	def loadInterfacedDecks(self):
		player = self.players[0]
		self.interfacedDecks.append(InterfacedDeckDescriptor(player,player.deckType))
	
	def loadRules(self):
		return self.rules
	
	def refreshUiVars(self):
		self.uiVars["round_count"] = str(self.round_count)
		self.uiVars["game_count"] = str(self.game_count)
		self.uiVars["stack_len"]= str(len(self.board.stock.cards))
		self.uiVars["info"]= self.players[0].messages[-1].text if len(self.players[0].messages) >= 1 else ""
		self.uiVars["debug"]= self.debug
		self.uiVars["nb_players"]= self.game_params["nb_players"] 
		
		sum_auction = 0
		for i in range(0,len(self.players)):
			self.uiVars["P"+str(i)+"current_score"]=str(self.players[i].current_score)
			self.uiVars["P"+str(i)+"round_won"]=str(self.players[i].round_won)
			self.uiVars["P"+str(i)+"auction"]=str(self.players[i].auction) 
			self.uiVars["P"+str(i)+"score"]=str(self.players[i].score)
			self.uiVars["P"+str(i)+"victory"]=str(self.players[i].victory) 
			self.uiVars["P"+str(i)+"nature"]=self.players[i].nature
			self.uiVars["P"+str(i)+"name"]=self.players[i].name
			self.uiVars["P"+str(i)+"tag"]=self.players[i].tag
			sum_auction= sum_auction + self.players[i].auction
		self.uiVars["sum_auction"] = str(sum_auction)	

class GameFactory():
	def __init__(self,general_params,game_params):
		self.general_params = general_params
		self.game_params = game_params

	def getGame(self):
		return Game(self.general_params)

def emptyCard():
	card = Card("",0,"",0,"")
	card.hidden=False
	return card


def loadParams(filename):
	#print("Now loading : " + filename)
	if not os.path.exists(filename):
		file = open(filename,"w")
		json.dump({},file)
		file.close()

	file = open(filename,"r")
	dictionary = json.load(file)
	file.close()
	return dictionary

def loadCardsOwned(playerName):
	filename = os.path.join(os.getcwd(),"players/"+playerName+".json")
	return loadParams(filename)
	

def listCardsOwned(player,cards_ref=None):
	list_cards = []
	for  key, value in player.cardsOwned.items() :
		for i in range(0,value):
			compl = ""
			if cards_ref is not None :
				compl = cards_ref[key].getInfo() 
			list_cards.append(key + " - " + compl + " - " + str(i+1))
	return list_cards

def getCardName(cardNameDisplayed):
	return cardNameDisplayed.split("-")[0].strip()
	
def saveParams(filename, dictionary):
	#print("Now loading : " + filename)
	file = open(filename,"w")
	json.dump(dictionary,file)
	file.close()


