import pygame

from .card_game import *
from .card_AI import *

# Define the colors:
#----------------------
AQUA = (0,255,255)
BLACK = (0,0,0)
GREEN = (0,128,0)
OLIVE = (128,128,0)
TEAL = (0,128,128)
WHITE = (255,255,255)
RED = (237,0,0)
#-----------------------

	
class CardInterface(object):
	def __init__ (self,x,y,w,h,name,index,marked,handle):
		self.rect = pygame.Rect(x,y,w,h)
		self.y=y
		self.x=x
		self.name = name
		self.index=index
		self.marked=marked
		self.handle=handle

class DeckInterface(object):
		
	VERTICAL=10
	HORIZONTAL=11
	
	def __init__(self,x,y,w,h,int1,int2,name,type,orientation, deckDisplayManager,hollow,nbmax):
		self.cardInterfaces = []
		self.deckInterfaceType = type
		self.x=x
		self.y=y
		self.width=w
		self.height=h
		self.int1=int1
		self.int2=int2
		self.name=name
		self.orientation = orientation
		self.deckDisplayManager = deckDisplayManager 
		self.hollow = hollow
		self.nbmax = nbmax
	
	def interfaceCards(self):
		cardList = self.deckDisplayManager.getList(self.deckInterfaceType)
		self.cardInterfaces = []
		for i in range(0,len(cardList)):
			x=self.x
			y=self.y
			a, b = divmod(i, self.nbmax) 
			if(self.orientation == DeckInterface.HORIZONTAL):
				y=y+(a*self.height)+self.int2*a
			else:
				x=x+(a*self.width)+self.int2*a

			if(self.orientation == DeckInterface.HORIZONTAL):
				x=x+(b*self.width/self.int1)+b*self.int2
			else:
				y=y+(b*self.height/self.int1)+b*self.int2
			
			name=""
			marked=False
			handle=False
			if(cardList[i] is not None):
				marked = cardList[i].marked
				handle = cardList[i].handle
				if(cardList[i].hidden):
					name="back"
				else: 
					name=cardList[i].name
			self.cardInterfaces.append(CardInterface(x,y,self.width,self.height,name,i,marked,handle))
	
class DeckDisplayManager(object):
	def __init__(self,deck):
		self.deck = deck
		
	def getList(self, deckType):
		if deckType == Deck.STOCK or deckType == Deck.WASTE:
			return [self.deck.showFront()]
		elif deckType == Deck.SELECTED:
			return self.deck.getSelected()
		else:
			return self.deck.cards if len(self.deck.cards) >= 1 else [None]
		
class InterfaceManager(object):
	def __init__(self):
		self.deckInterfaces = []
	
	def cleanDisplayer(self):
		self.deckInterfaces = []
		
	def addDeckInterface(self, deckInterface) :
		self.deckInterfaces.append(deckInterface)
		
	def display(self,screen,card_dict):
		for d in self.deckInterfaces:
			#print(d.name +" " +str(len(d.cardInterfaces)))
			if not d.hollow :
				pygame.draw.rect(screen,BLACK,[d.x-2,d.y-2,d.width+3,d.height+3],2)

			for c in d.cardInterfaces:
				draw_card(c,screen,card_dict,d.width,d.height,d.hollow)
				
	def input(self,x,y,playerName):
		for d in self.deckInterfaces:
			for c in reversed(d.cardInterfaces):
				#print(c.name)
				if(c.rect.collidepoint(x,y)) :
					#print("mouse : " + str(x) + ':' + str(y) + " -> " + d.name + "->" + c.name)
					return MessageDeck( Message.GAME,d.deckInterfaceType, playerName, d.name, c.index)

	def inputSort(self,x,y,playerName):
		for d in self.deckInterfaces:
			for c in reversed(d.cardInterfaces):
				#print(c.name)
				if(c.rect.collidepoint(x,y)) :
					#print("mouse : " + str(x) + ':' + str(y) + " -> " + d.name + "->" + c.name)
					return MessageDeck( Message.GAME,Deck.SORT, playerName, d.name, c.index)

	def inputValue(self,value,playerName):
		return MessageValue( Message.GAME,Deck.CHOICE, playerName, "input : " + playerName + " : " + str(value), value)

	def outputValue(self,value,playerName):
		return MessageValue( Message.CHOICE,Deck.CHOICE, playerName, "output", value)


def sendMessagePlayer(player,text):
	player.sendMessage(Message(Message.INFO, Deck.PLAYER, player.name, text))
								 
def loadCards(file_name):
	fic = open(file_name,'r')
	cards = []
	
	for line in fic :
		val = line.rstrip('\n').split(",")
		if len(val) ==  5:
			name = val[0]
			#print(name+" -> "+nameFic)
			card = Card(name,val[1],val[2],int(val[3]),val[4])
			cards.append(card)
			
	

	return cards

def loadCardsRef(cards):
	cards_ref = {}
	for c in cards:
		cards_ref[c.name] = c

	return cards_ref

def loadCardsDict(file_name,back_name):
	fic = open(file_name,'r')
	card_dict = { }
	for line in fic :
		val = line.rstrip('\n').split(",")
		if len(val) ==  2:
			nameFic = val[1]
			name = val[0].strip()
			#print(name+" -> "+nameFic)
			img = pygame.image.load(os.path.join(os.getcwd(),nameFic.strip())).convert()
			card_dict[name] = img
	
	
	imagename = os.path.join(os.getcwd(),back_name)
	img = pygame.image.load(imagename).convert()
	card_dict["back"] = img

	return  card_dict

def draw_card(card,screen,card_dict,w,h,hollow):
	"""This will draw a card on the screen"""
	color=BLACK
	if card.handle:
		color=AQUA
	if card.marked:
		color=RED
		
	if not hollow or card.name != "":
		pygame.draw.rect(screen,color,[card.x-2,card.y-2,w+3,h+3],2)
		
	if card.name != "":
		picture = pygame.transform.scale(card_dict[card.name], (w, h))
		screen.blit(picture,[card.rect.left,card.y])

class InterfaceGameManager(object):

	def __init__(self):
		self.deckInterfaces = []
	
	def addDeckInterface(self,deckInterface):
		self.deckInterfaces.append(deckInterface)
		
	def interface(self,interfaceManager):
		for d in self.deckInterfaces:
			interfaceManager.addDeckInterface(d)
	
	def update(self,game):
		if game.changed :
			for d in self.deckInterfaces:
				d.interfaceCards()
			game.changed = False


class GameManager(object):
	DEBUG_MODE=1
	STEP_UP=2
	STEP_BACK=3
	MOUSE_CLICK=4
	GAME_PARAM=5
	NEW_GAME=6
	RETRY=7
	SAVE_PARAMS=8
	GAME_INPUT=9
	OUTPUT_TEST = 10
	PYGAME_GAME_PARAM=25
	PYGAME_INPUT=26

	def __init__(self,game,interfaceManager,cardList,cards_ref,eventManager,aiManager,reflexionTime):
		self.game=game
		self.interfaceManager=interfaceManager
		self.cards=cardList
		self.cards_ref=cards_ref
		self.eventManager=eventManager
		self.aiManager=aiManager
		self.chronoGame = ChronoPy(reflexionTime)
		self.chronoAI = ChronoPy(reflexionTime)
		self.debug_mode = False
		self.previousState=None
		self.firstState=None
		#self.newGameState=None
		self.game.game_count=1
		self.game.round_count=1
		self.output_messages = []

	def initialisation(self):
		self.game.fullAI = False #self.game.getNbPlayers() == self.aiManager.getNbPlayers()
		if self.game.fullAI : 
			self.reflexionTime = 0
			self.chronoGame = ChronoPy(self.reflexionTime)
			self.chronoAI = ChronoPy(self.reflexionTime)

		self.game.board.initialisation(self.cards, self.cards_ref)
		#print("board :" + str(len(self.game.board.stock_init.cards)))
		self.game.board.emptyWaste()
		self.game.changed = True
		#self.game.game_count=1
		self.game.start()
		self.previousState = copy.deepcopy(self)
	
	def event(self, events):
		return self.eventManager.event(events)

	def step(self, events):

		self.output_messages = []

		if self.game.state == Game.CONFIRMATION :
			self.chronoGame.raz()

		if self.game.state != Game.ACTION or self.chronoGame.check(self.game.fullAI) :
			#self.game.step()
			ret, dic = self.event(events)
			#print("retour :" + str(ret))

			if ret == GameManager.STEP_BACK or ret == GameManager.NEW_GAME or ret == GameManager.RETRY or ret == GameManager.SAVE_PARAMS :
				return ret

			if ret == GameManager.DEBUG_MODE:
				self.debug_mode = not self.debug_mode
				#print("Debug : " + str (self.debug_mode))
				self.game.debug = "Debug : " + str (self.debug_mode)

			if ret == GameManager.MOUSE_CLICK: 
				pos = dic["pos"]
				if(dic["button"] == 1 ):
					self.game.sendMessage(self.interfaceManager.input(pos[0],pos[1],self.eventManager.name))
				elif(dic["button"] == 3 ):
					self.game.sendMessage(self.interfaceManager.inputSort(pos[0],pos[1],self.eventManager.name))

			if ret == GameManager.GAME_PARAM:
				self.game_params[dic["key"]] = dic["value"]
				#print(self.game_params)

			if ret == GameManager.GAME_INPUT:
				#print(dic)
				self.game.sendMessage(self.interfaceManager.inputValue(dic["value"],self.eventManager.name))

			if ret == GameManager.OUTPUT_TEST:
				self.game.addOutputMessage(self.interfaceManager.outputValue({"title":"TRT","text":"choisir une valeur","value":{"bet":[1,2,3,4,5,6]}},self.eventManager.name))

			if (not self.debug_mode or ret == GameManager.STEP_UP):
				if (self.debug_mode):
					self.previousState = copy.deepcopy(self)
				else :
					self.previousState = None
				self.game.step()


				if self.aiManager is not None :
					#gestion du temps de reflexion pour les IA
					if self.chronoAI.check(self.game.fullAI):
						messages = self.aiManager.play(self.game)
						for m in messages :
							self.game.sendMessage(m)
				
				self.game.readMessages()

			for m in self.game.output_messages:
				if m.messageType == Deck.CHOICE and m.playerName == self.eventManager.name and m.playerName not in list(map(lambda x: (x.name if x.ai.level != 0 else "anonym"), self.aiManager.players)):
                        	      self.output_messages.append(m.value)

			self.game.cleanOutputMessages()
		return 0
	
	def refresh(self,screen,card_dict,interfaceGameManager,uiManager,backgroundManager):
		interfaceGameManager.update(self.game)
		backgroundManager.display(screen)
		self.interfaceManager.display(screen,card_dict)
		self.game.refreshUiVars()
		uiManager.display(self.game.uiVars,screen)
		
class EventManager(object):
	def __init__(self, name):
		self.name=name

	def getEvents(self):
		return pygame.event.get()

	def event(self, events):
		ret=0
		#message=None
		dic = None
		#events = self.getEvents()
		#print(events)
		for event in events: # User did something
			#print(event)
			#print("Mouse event " + str(event.type) + " "  + str(pygame.MOUSEBUTTONDOWN))
			
			if event.type == pygame.KEYDOWN:
				#print("key :" + chr(event.key))
				if event.key == pygame.K_d : ret = GameManager.DEBUG_MODE
				elif event.key == pygame.K_f : ret = GameManager.STEP_UP
				elif event.key == pygame.K_b : ret = GameManager.STEP_BACK
				elif event.key == pygame.K_n : ret = GameManager.NEW_GAME
				elif event.key == pygame.K_r : ret = GameManager.RETRY
				elif event.key == pygame.K_s : ret = GameManager.SAVE_PARAMS
				elif event.key == pygame.K_a : ret = GameManager.OUTPUT_TEST

			if event.type == pygame.MOUSEBUTTONDOWN:
				continue

			if event.type == pygame.MOUSEBUTTONUP:
				#print("OK")
				dic = event.dict
				ret = GameManager.MOUSE_CLICK
				#pos = event.dict["pos"]
				#message = interfaceManager.input(pos[0],pos[1],self.name)
				#print(dic)


			if event.type == pygame.USEREVENT:
				dic = event.dict
				#print(event.dict)
				if(dic["type_event"] == "input") :
					ret = GameManager.GAME_INPUT
				else:
					ret = GameManager.GAME_PARAM


		return ret, dic



class BackgroundManager(object):
	def __init__(self,width,height,picture,color):
		font = pygame.font.Font(None,25)
		self.height = height
		self.width = width
		self.color = color
		self.picture = picture

	def display(self,screen):
		if self.picture == None:
			screen.fill((self.color))
		else :
			pic = pygame.transform.scale(self.picture, (self.width, self.height))
			screen.blit(pic,[0,0])

class UIManager(object):
	
	def __init__(self,width,height,uiElements):
		font = pygame.font.Font(None,25)
		self.text = font.render("Fini !",True,BLACK)
		self.height = height
		self.width = width
		self.uiElements = uiElements
	
	
	def display(self,uiVars,screen):
		
		for uie in self.uiElements:
			font = pygame.font.SysFont(uie.font,uie.size)
			x = uie.x
			y = uie.y
			c = (uie.r,uie.g,uie.b)
			if (uie.typele == "liste") :
				#print("NB_players"+str(uiVars["nb_players"])) 
				for i in range(0,int(uiVars["nb_players"])):
					if(uie.orientation == "v"):
						yi = y + (uie.h+uie.interval)*i 
						xi = x
					else:
						yi = y
						xi = x  + (uie.w+uie.interval)*i 

					text = font.render(uiVars["P"+str(i)+uie.var],True,c)
					screen.blit(text,[xi,yi])

			elif (uie.typele == "element") :
				if uiVars.get(uie.var) is not None :
					text = font.render(uiVars[uie.var],True,c)
					screen.blit(text,[x,y])

			elif (uie.typele == "constante") :
				text = font.render(uie.var,True,c)
				screen.blit(text,[x,y])

		pygame.draw.rect(screen,WHITE,[0,self.height-15,self.width,15])
		
		text = font.render(uiVars["info"],True,BLACK)
		screen.blit(text,[0,self.height-15])
		text = font.render("| " + uiVars["debug"],True,BLACK)
		screen.blit(text,[self.width - self.width/3,self.height-15])
		#self.displayPlayers(game.players,screen)
		#self.displayInfo(game,screen)


	
class UIManagerFactory(object):
	def __init__(self,w,h,uiElements):
		self.w = w
		self.h = h
		self.uiElements = uiElements

	def getUIManager(self):
		return UIManager(self.w,self.h,self.uiElements)

class ChronoPy(object):
	def __init__(self,interval):
		self.last = pygame.time.get_ticks()
		self.interval = interval    
		
	def check(self,fullAI):
		now = pygame.time.get_ticks()
		if now - self.last >= self.interval or fullAI:
			self.raz()
			return True
		return False
	
	def raz(self):
		self.last = pygame.time.get_ticks()
		return 0

class GameManagerFactory():

	def __init__(self,gameFactory, aIFactory, loadCards):
		self.gameFactory = gameFactory
		self.aIFactory = aIFactory
		self.loadCards = loadCards
		
	def getGameManager(self, general_params, algoAI=None ):
		#Game
		game = self.gameFactory.getGame()
		# Players, Events and AI
		aiManager = playersMaker(game,algoAI,self.aIFactory)
		game.loadInterfacedDecks()
		eventManager = EventManager(game.players[0].name)
		# Rules
		game.loadRules()
		
		# Cards
		cards  = self.loadCards(general_params["cards"])
		cards_ref = loadCardsRef(cards)

		reflexionTime = 1000

		# Interface
		interfaceManager = InterfaceManager()
		
		# GameManager
		gameManager = GameManager(game,interfaceManager,cards, cards_ref,eventManager,aiManager,reflexionTime)
		
		return gameManager


class InterfaceGameManagerFactory(object):
	
	def getInterfaceGameManager(self,game):
		return None

class InterfaceLine(object):
	def __init__(self,name,x,y,w,h,int1,int2,orientation,hollow,nbmax):
		self.name=name
		self.x=x
		self.y=y
		self.h=h
		self.w=w
		self.int1=int1
		self.int2=int2
		self.orientation= orientation
		self.hollow=hollow
		self.nbmax=nbmax

def interfaceLineFromFile(fic):
	interfacelines = []
	for line in fic:
		l=line.rstrip().split(";")
		if len(l) == 10:
			hollow = False
			if l[8] == "h" : hollow = True
			#print (str(hollow) + ":"+ l[8] )
			orientation = DeckInterface.HORIZONTAL
			if l[7] == "v":
				orientation = DeckInterface.VERTICAL
                          
			interfacelines.append(InterfaceLine(l[0],int(l[1]),int(l[2]),int(l[3]),int(l[4]),int(l[5]),int(l[6]),orientation,hollow,int(l[9])))
	return interfacelines

class UIElement(object):
	def __init__(self,var,font,size,orientation,x,y,w,h,r,g,b,typele,interval):
		self.var=var
		self.font=font
		self.size=size
		self.orientation = orientation
		self.x=x
		self.y=y
		self.h=h
		self.w=w
		self.r=r
		self.g=g
		self.b=b
		self.interval=interval
		self.typele=typele

#P1name;comicsansms;size;v;0;0;10;10;r;g;b;typele;interval
def uiElementFromFile(fic):
	uiElements = []
	for line in fic:
		l=line.rstrip().split(";")
		if len(l) == 13:
			hollow = False
			if l[8] == "h" : hollow = True
			#print (str(hollow) + ":"+ l[8] )
			orientation = DeckInterface.HORIZONTAL
			if l[7] == "v":
				orientation = DeckInterface.VERTICAL
                          
			uiElements.append(UIElement(l[0],l[1],int(l[2]),l[3],int(l[4]),int(l[5]),int(l[6]),int(l[7]),int(l[8]),int(l[9]),int(l[10]),l[11],int(l[12])))
	return uiElements

class InterfaceGameGenericManagerFactory(InterfaceGameManagerFactory):

	def __init__(self, interfaces):
		self.interfaces = interfaces
		
	def getInterfaceGameManager(self,game):
		interfaceGameManager = InterfaceGameManager()
		for i in range(0,len(self.interfaces)):
			#print(self.interfaces[i].name + ":" + game.interfacedDecks[i].name)
			deckInterface = DeckInterface(self.interfaces[i].x,self.interfaces[i].y,self.interfaces[i].w,self.interfaces[i].h,self.interfaces[i].int1,self.interfaces[i].int2,game.interfacedDecks[i].deck.name,game.interfacedDecks[i].deckType,self.interfaces[i].orientation,DeckDisplayManager(game.interfacedDecks[i].deck),self.interfaces[i].hollow,self.interfaces[i].nbmax)
			interfaceGameManager.addDeckInterface(deckInterface)

		
		return interfaceGameManager


class GameScene(object):
	NOT_INIT=0
	INIT=1
	OVER=2
	STANDBY=3
	RESET=4

	def __init__(self,general_params,game_params,game_options=None):
		self.state = GameScene.NOT_INIT
		self.general_params = general_params
		self.game_params = game_params
		self.game_options = game_options
	
	def initialisation(self,screen,card_dict):
		self.state = GameScene.INIT
		
class GameLogic(GameScene):

	def __init__(self,general_params,game_params,gameManagerFactory, interfaceGameManagerFactory,uiManagerFactory,backgroundManager,algoAI=None):
		super().__init__(general_params,game_params)
		self.gameManagerFactory = gameManagerFactory
		self.interfaceGameManagerFactory = interfaceGameManagerFactory
		self.done = False
		self.gameManager = None
		self.interfaceGameManager = None
		self.backgroundManager = backgroundManager
		self.uiManagerFactory = uiManagerFactory
		self.uiManager = None
		self.algoAI = algoAI

	def initialisation(self,screen,card_dict):
		super().initialisation(screen,card_dict)
		self.gameManager = self.gameManagerFactory.getGameManager(self.general_params,self.algoAI)
		if self.gameManager is not None :
			self.interfaceGameManager = self.interfaceGameManagerFactory.getInterfaceGameManager(self.gameManager.game)
			self.uiManager = self.uiManagerFactory.getUIManager()
			if self.interfaceGameManager is not None :
				self.screen= screen
				self.card_dict = card_dict
				self.interfaceGameManager.interface(self.gameManager.interfaceManager)
				self.gameManager.initialisation()
				
				
	def step(self, events):
		old_state=self.gameManager.game.state
		#print("etat :" +str(old_state))
		ret = self.gameManager.step(events)
		#if old_state == self.gameManager.game.INITIALISATION and self.gameManager.game.state != self.gameManager.game.INITIALISATION:
		#	self.gameManager.newGameState = copy.deepcopy(self.gameManager)
		if old_state == self.gameManager.game.DISTRIBUTION and self.gameManager.game.state != self.gameManager.game.DISTRIBUTION and not self.gameManager.game.fullAI:
			self.gameManager.firstState = copy.deepcopy(self.gameManager)
		if (ret == GameManager.NEW_GAME):
			self.state = GameScene.RESET
			#self.initialisation(self.screen,self.card_dict)
			#old_state =self.gameManager.newGameState
			#self.gameManager = self.gameManager.newGameState
			#self.gameManager.newGameState = copy.deepcopy(old_state)
			#self.interfaceGameManager = self.interfaceGameManagerFactory.getInterfaceGameManager(self.gameManager.game)
			#self.gameManager.interfaceManager = InterfaceManager()
			#self.interfaceGameManager.interface(self.gameManager.interfaceManager)
			#self.gameManager.game.changed = True


		if (ret == GameManager.STEP_BACK and self.gameManager.previousState is not None):
			self.gameManager = self.gameManager.previousState
			#gameManager.game = gameManager.game.previousState
			self.interfaceGameManager = self.interfaceGameManagerFactory.getInterfaceGameManager(self.gameManager.game)
			self.gameManager.interfaceManager = InterfaceManager()
			self.interfaceGameManager.interface(self.gameManager.interfaceManager)
			self.gameManager.debug_mode = True
			self.gameManager.game.changed = True

		if (ret == GameManager.RETRY and self.gameManager.firstState is not None):
			old_state =self.gameManager.firstState
			self.gameManager = self.gameManager.firstState
			self.gameManager.firstState = copy.deepcopy(old_state)
			self.interfaceGameManager = self.interfaceGameManagerFactory.getInterfaceGameManager(self.gameManager.game)
			self.gameManager.interfaceManager = InterfaceManager()
			self.interfaceGameManager.interface(self.gameManager.interfaceManager)
			#self.gameManager.debug_mode = True
			self.gameManager.game.changed = True

		if (ret == GameManager.SAVE_PARAMS):
			self.gameManager.game.saveGameParams()

		# --- Game logic should go here
		if (not self.gameManager.game.fullAI or (self.gameManager.game.fullAI and (self.gameManager.game.state  == Game.VALIDATION or self.gameManager.game.state  == Game.AUCTION or self.gameManager.game.state  ==  Game.GAME_OVER)) ):
			self.gameManager.refresh(self.screen,self.card_dict,self.interfaceGameManager,self.uiManager,self.backgroundManager)
			pygame.display.flip()
		
	
		if self.gameManager.game.isGameOver() and self.algoAI is not None and not self.algoAI.isOver():
			#print("reinit")
			self.algoAI.step(self.gameManager.game.players[0])
			if not self.algoAI.isOver():
				self.initialisation(self.screen,self.card_dict,self.gameManager.game.general_params)
			else:
				self.done = True
		
		if self.gameManager.game.state == Game.REINIT_PLAYER :
			self.aiManager = playersMaker(self.gameManager.game,self.algoAI,self.gameManagerFactory.aIFactory)
			self.gameManager.game.state = Game.INITIALISATION
       
	def getOutputMessages(self):
		return self.gameManager.output_messages

	def clearOutputMessages(self):
		self.gameManager.output_messages = []

class GameLogicFactory:

	def __init__(self, GameManagerFactory):
		self.GameManagerFactory = GameManagerFactory

	def getGameScene(self,general_params,game_params,game_options):
		# screen and game #
		# Set the width and height of the screen [width, height]
		#screen = pygame.display.set_mode([SCREEN_WIDTH,SCREEN_HEIGHT])
		#cards, card_dict = loadTRTCards("TRT_cards.csv")
		basePath = os.getcwd()
		w = general_params["screen_width"]
		h = general_params["screen_height"]
		imagePathBkg = os.path.join(basePath, general_params["background"])
		imgBkg = pygame.image.load(imagePathBkg).convert()
		picture = pygame.transform.scale(imgBkg, (w,h-15))

		basePath = os.getcwd()
		cpl = ""
		if general_params["multi_fic_config"]:
			cpl = str(game_params["nb_players"])
		ccfgPath = os.path.join(general_params["fic_config"]+cpl+general_params["extension_fic_config"])
		fic = open(ccfgPath,'r')
		interfaceLines =interfaceLineFromFile(fic)
		fic.close()

		ccfgPath = os.path.join(general_params["fic_interface"]+cpl+general_params["extension_fic_interface"])
		fic = open(ccfgPath,'r')
		uiElements = uiElementFromFile(fic)
		fic.close()

		algoAI = None
		if  game_params["benchmarkAI"] :
			fic = game_params["log_file_benchmark"]  + "_" + str(datetime.datetime.now()) + ".csv"
			nbGeneration = game_params["nb_generations_algo"]
			nbIndividus = game_params["nb_individus_algo"]
			algoAI = AlgoGenetiqueTAFFactory().getAlgoGenetique(nbGeneration,nbIndividus,fic)


		#Manager
		
		backgroundManager = BackgroundManager(w,h,picture,(0,128,128))
		#interfaceGameManager.update(game)
		""" fin int game Manager """
		#Loop until the user clicks the close button.
		#gameLoop = GameLoop(GameManagerFactoryTRT(),InterfaceGameTRTManagerFactory(),20)
		return GameLogic(general_params,game_params,self.GameManagerFactory,InterfaceGameGenericManagerFactory(interfaceLines),UIManagerFactory(w,h,uiElements),backgroundManager,algoAI)



class GameLoop(object):
	def __init__(self,general_params,game_params,gameSceneFactoryList,transitionManager=None, game_options=None,tick=20):
		self.gameScenes = []
		self.current_gameScene = 0
		self.clock = None
		self.transitionManager = transitionManager
		self.tick = tick
		self.done = False
		self.gameSceneFactoryList = gameSceneFactoryList
		#for gameSceneFactory in gameSceneFactoryList :
		#	self.gameScenes.append(gameSceneFactory.getGameScene(general_params,game_params))
		self.gameScenes.append(gameSceneFactoryList[0].getGameScene(general_params,game_params,game_options))
		self.general_params = general_params
		self.card_dict = None
		self.screen = None
		self.game_params = game_params
		self.game_options  = game_options
		
		
	
	def initialisationScene(self):
		print(self.current_gameScene)
		self.gameScenes[self.current_gameScene].initialisation(self.screen,self.card_dict)

	def initialisation(self,screen,card_dict):
		self.card_dict = card_dict
		self.screen = screen
		self.initialisationScene()
		if  not self.game_params["benchmarkAI"]  and not self.game_params["fullAI"]  :
			self.tick = 1000
		self.clock = pygame.time.Clock()

				
	def step(self):
		self.clearOutputMessages()
		events = pygame.event.get()
		for event in events :
			if event.type == pygame.QUIT:
				self.done = True
		
		if not self.done :
			if self.transitionManager is not None :
				self.done =  not self.transitionManager.transition(self)
			if not self.done :
				self.gameScenes[self.current_gameScene].step(events)
			#print(self.done )

		# --- Limit to 20 frames per second
		self.clock.tick(self.tick)
		

	def loop(self,screen,card_dict):
		while not self.done :
			print("step")
			self.step()
		# Close the window and quit.
		# If you forget this line, the program will 'hang'
		# on exit if running from IDLE.
		print("Quit!!!!")
		pygame.quit()
       
	def getOutputMessages(self):
		return self.gameScenes[self.current_gameScene].getOutputMessages()

	def clearOutputMessages(self):
		self.gameScenes[self.current_gameScene].clearOutputMessages()

class GameMenuNbPlayers(GameScene):
	def __init__(self,title,general_params,game_params):
		super().__init__(general_params,game_params)
		self.title = title
		self.outputMessages = []


	def getOutputMessages(self):
		return self.outputMessages

	def clearOutputMessages(self):
		self.outputMessages = []

	def step(self,events):
		for event in events :
			if event.type == pygame.USEREVENT:
				dic =	 event.dict
				#print(event.dict)
				if(dic["type_event"] == "input") :
					print("Value : " + str(dic["value"]))
					print("Value : " + str(dic["value"][0]))
					self.game_params["nb_players"]=int(dic["value"][0])
					self.state = GameScene.OVER
					return 

			if self.outputMessages == [] and self.state == GameScene.INIT :
				print("STATE : " + str(self.state))
				list_nb_players =  []
				for i in range (self.game_params["nb_min_players"],self.game_params["nb_max_players"]+1):
					list_nb_players.append(i)
				value = {"title":self.title,"text":"nombre de joueurs","value":{"nb_joueurs":list_nb_players}}
				self.outputMessages.append(value)
				self.state = GameScene.STANDBY

class GameMenuPlayers(GameScene):
	def __init__(self,title,general_params,game_params,game_options):
		super().__init__(general_params,game_params,game_options)
		self.title = title
		self.outputMessages = []


	def getOutputMessages(self):
		return self.outputMessages

	def clearOutputMessages(self):
		self.outputMessages = []

	def step(self,events):
		for event in events :
			if event.type == pygame.USEREVENT:
				dic =	 event.dict
				#print(event.dict)
				if(dic["type_event"] == "input") :
					print("Value : " + str(dic["value"]))
					choice=self.game_options[dic["value"][0]]
					print(choice)
					i = 0
					for player in choice["players"] :
						self.game_params["player" + str(2+i)] = player
						print("player" + str(2+i) + ":")
						print( self.game_params["player" + str(2+i)])
						i = i+1
					self.game_params["nb_games"] = len(choice["players"])
					self.state = GameScene.OVER
					return 

			if self.outputMessages == [] and self.state == GameScene.INIT :
				print("STATE : " + str(self.state))
				list_players =  []
				for key in self.game_options :
					list_players.append(key)
				value = {"title":self.title,"text":"joueurs","value":{"nb_joueurs":list_players}}
				self.outputMessages.append(value)
				self.state = GameScene.STANDBY


class GameMenuNbPlayersFactory(object):
	def __init__(self,title):
		self.title = title
	def getGameScene(self,general_params,game_params,game_options):
		return GameMenuNbPlayers(self.title,general_params,game_params)
		
class GameMenuPlayersFactory(object):
	def __init__(self,title):
		self.title = title
	def getGameScene(self,general_params,game_params,game_options):
		return GameMenuPlayers(self.title,general_params,game_params,game_options)

class SimpleTransitionManager(object):
	def transition(self, gameLoop):
		if gameLoop.gameScenes[gameLoop.current_gameScene].state == GameScene.OVER:	
			if gameLoop.current_gameScene < len(gameLoop.gameSceneFactoryList)-1:
				gameLoop.current_gameScene = gameLoop.current_gameScene + 1
				gameLoop.gameScenes.append(gameLoop.gameSceneFactoryList[gameLoop.current_gameScene].getGameScene(gameLoop.general_params,gameLoop.game_params,gameLoop.game_options))
				gameLoop.initialisationScene()
			else :
				return False
		if gameLoop.gameScenes[gameLoop.current_gameScene].state == GameScene.RESET:	
			gameLoop.current_gameScene = 0
			gameLoop.gameScenes = []
			gameLoop.gameScenes.append(gameLoop.gameSceneFactoryList[gameLoop.current_gameScene].getGameScene(gameLoop.general_params,gameLoop.game_params,gameLoop.game_options))
			gameLoop.initialisationScene()
		return True


