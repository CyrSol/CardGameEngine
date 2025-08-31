import random
from .card_game import *
from operator import itemgetter



##########################################################################################################
##########################################################################################################
class AIHuman(AI):
	def __init__(self):
		AI.__init__(self,0,'AI_Human')

	def play(self,game,player):
		if game.state == Game.PREPARATION :
			#cardsList = listCardsOwned(player)
			#for i in range(0,5):
				#print(i)
			#	e = cardsList.pop(random.randint(0,len(cardsList)-1))
				#print(e)
			#	c = game.board.getCardFromName(e)
			#	player.addBack(c)
			if len(player.cards) == 0:
				player.cardsPlayable = listCardsOwned(player,game.board.getCompl())
			return MessageDeck(Message.GAME,Deck.PLAYER,player.name,player.name,0)

		elif game.state == Game.RECUPERATION :
			#cardsList = listCardsOwned(player)
			#for i in range(0,5):
				#print(i)
			#	e = cardsList.pop(random.randint(0,len(cardsList)-1))
				#print(e)
			#	c = game.board.getCardFromName(e)
			#	player.addBack(c)
			if player.nb_picked == 0:
				player.cardsPickable = []
				i = 1
				for c in game.cardsPickable:
					player.cardsPickable.append(c.tag + " - " + c.getInfo() + " - " +  str(i))
					i = i + 1
			return MessageDeck(Message.GAME,Deck.PLAYER,player.name,player.name,0)
	

class AITRTRandom(AI):
	def __init__(self):
		AI.__init__(self,0,'AI_TRT_Random')

	def play(self,game,player):
		#print(player.name + " -> " + str(game.state) + ";" + str(len(player.cards)))
			
		if game.state == Game.SELECTION and len(player.selected) == 0:
			if len(player.cards) > 0 :
				index = random.randrange(0,len(player.cards))
				return MessageDeck(Message.GAME,Deck.PLAYER,player.name,player.name,index)
			
		#elif game.state == Game.CONFIRMATION:
			#return MessageDeck(Message.GAME,Deck.SELECTED,player.name,player.name,0)
			
		elif game.state == Game.SELECTION and len(player.selected) == 1:
			listing = game.free_rooms()
			j,i = listing[random.randint(0,len(listing)-1)]
			#index = random.randint(0,len(game.decksTab)-1)
			#i = random.randint(0,len(game.decksTab[index].cards)-1)
			#print(str(j) + ":" + str(i))
			return MessageDeck(Message.GAME,Deck.BOARD,player.name,game.decksTab[j].name,i)

		elif game.state == Game.VALIDATION:
			return MessageDeck(Message.GAME,Deck.BOARD,	player.name,game.decksTab[0].name,0)

class AITRTMiniMax(AI):
	def __init__(self):
		AI.__init__(self,0,'AI_TRT_MiniMax')
		self.i=-1
		self.j=-1

	def play(self,game,player):
		#print(player.name + " -> " + str(game.state) + ";" + str(len(player.cards)))
			
		if game.state == Game.SELECTION and len(player.selected) == 0:
			self.i=-1
			self.j=-1
			score = player.score
			listing = game.free_rooms()
			current_player = game.player
			scores=[]
			for c in player.cards:
				for k,l in listing:
					self.i = l
					self.j = k
					#print(c.name + "->" +str(k) + ":" + str(l) + "/" + str(len(player.selected)))
					index = player.cards.index(c)
					game_simul = copy.deepcopy(game)
					game_simul.sendMessage(MessageDeck(Message.GAME,Deck.PLAYER,player.name,player.name,index))
					game_simul.readMessages()
					game_simul.step()
					while(current_player == game_simul.player):
						#print(c.name + "-->" +str(k) + ":" + str(l) + "/" + str(len(player.selected)))
						if(player.name in game_simul.awaited):
							m = game_simul.getPlayer(player.name).play(game_simul)
							#print(m.to_string())
							game_simul.sendMessage(m)
							game_simul.readMessages()
						game_simul.step()
					scores.append((index,k,l,game_simul.getPlayer(player.name).current_score))
			best_moves=[]
			score_max = max(scores,key=itemgetter(3))[3] 
			#print(scores)
			#print("Score max :" + str(score_max))
			for index,k,l,s in scores:
				if s == score_max :
					best_moves.append((index,k,l))
			index,k,l= best_moves[0]
			self.i = l
			self.j = k
			return MessageDeck(Message.GAME,Deck.PLAYER,player.name,player.name,index)

					
			
		#elif game.state == Game.CONFIRMATION:
			#return MessageDeck(Message.GAME,Deck.SELECTED,player.name,player.name,0)
			
		elif game.state == Game.SELECTION and len(player.selected) == 1:
			#index = random.randint(0,len(game.decksTab)-1)
			#i = random.randint(0,len(game.decksTab[index].cards)-1)
			#print(str(j) + ":" + str(i))
			return MessageDeck(Message.GAME,Deck.BOARD,player.name,game.decksTab[self.j].name,self.i)

		elif game.state == Game.VALIDATION:
			return MessageDeck(Message.GAME,Deck.BOARD,player.name,game.decksTab[0].name,0)	

class AITRTMiniMax2(AI):
	def __init__(self):
		AI.__init__(self,0,'AI_TRT_MiniMax2')
		self.i=-1
		self.j=-1

	def play(self,game,player):
		#print(player.name + " -> " + str(game.state) + ";" + str(len(player.cards)))
			
		if game.state == Game.SELECTION and len(player.selected) == 0:
			self.i=-1
			self.j=-1
			score = player.score
			listing = game.free_rooms()
			#print(listing)
			current_player = game.player
			scores=[]
			for c in player.cards:
				for k,l in listing:
					self.i = l
					self.j = k
					#print(c.name + "->" +str(k) + ":" + str(l) + "/" + str(len(player.selected)))
					index = player.cards.index(c)
					game_simul = copy.deepcopy(game)
					game_simul.sendMessage(MessageDeck(Message.GAME,Deck.PLAYER,player.name,player.name,index))
					game_simul.readMessages()
					game_simul.step()
					while(current_player == game_simul.player):
						#print(c.name + "-->" +str(k) + ":" + str(l) + "/" + str(len(player.selected)))
						if(player.name in game_simul.awaited):
							m = game_simul.getPlayer(player.name).play(game_simul)
							#print(m.to_string())
							game_simul.sendMessage(m)
							game_simul.readMessages()
						game_simul.step()
					sumPoints, nbPoints = game_simul.pointsExposed(current_player)
					note=game_simul.getPlayer(player.name).current_score*100
					#print (str(sumPoints)+ "x" + str(nbPoints))
					if nbPoints == 0:
						note = note+11
					else:
						note=note+int(sumPoints/nbPoints)
					scores.append((index,k,l,note))
			best_moves=[]
			score_max = max(scores,key=itemgetter(3))[3] 
			#print(scores)
			#print("Score max :" + str(score_max))
			for index,k,l,s in scores:
				if s == score_max :
					best_moves.append((index,k,l,s))
			index,k,l,s = best_moves[random.randint(0,len(best_moves)-1)]
			self.i = l
			self.j = k
			print(best_moves)
			print("Choix :" + str(index) + "->" + str(self.j) + ":" + str(self.i))
			return MessageDeck(Message.GAME,Deck.PLAYER,player.name,player.name,index)

					
			
		#elif game.state == Game.CONFIRMATION:
			#return MessageDeck(Message.GAME,Deck.SELECTED,player.name,player.name,0)
			
		elif game.state == Game.SELECTION and len(player.selected) == 1:
			#index = random.randint(0,len(game.decksTab)-1)
			#i = random.randint(0,len(game.decksTab[index].cards)-1)
			#print(str(j) + ":" + str(i))
			return MessageDeck(Message.GAME,Deck.BOARD,player.name,game.decksTab[self.j].name,self.i)

		elif game.state == Game.VALIDATION:
			return MessageDeck(Message.GAME,Deck.BOARD,player.name,game.decksTab[0].name,0)	


##########################################################################################################
##########################                  Algo génétique                      ##########################
##########################################################################################################


class ParametreAlgoGenetique():
	
	def __init__(self,mini,maxi,step):
		self.min=mini
		self.max=maxi
		self.step=step

	def mutation(self,value):
		rnd = random.randrange(0,4)
		if(rnd == 1):
			return round(random.uniform(self.min,self.max),2)
		elif(rnd == 2):
			return value
		else:
			rnd = random.randrange(0,1)
			fac = 1
			if (rnd == 0 or value == self.max):
				fac = -1
			return round(value + (fac*self.step),2)

	def aleatoire(self):
		return round(random.uniform(self.min,self.max),2)
		

class ElementAlgoGenetique():
	
	def __init__(self,params,values,fitScorePere=0):
		self.params=params
		self.values=values
		self.fitScore=0
		self.fitScorePere=fitScorePere
	
	def mutation(self):
		listValues=[]
		for i in range(0,len(self.params)):
			listValues.append(self.params[i].mutation(self.values[i]))
		return ElementAlgoGenetique(self.params,listValues,self.fitScore)

	def elementAleatoire(self):
		listValues=[]
		for i in range(0,len(self.params)):
			listValues.append(self.params[i].aleatoire())
		return ElementAlgoGenetique(self.params,listValues,0)

	def croisement(self,element):
		listElements=[]
		listElements.append(self)
		listElements.append(element)
		listParams=[]
		listValues=[]		
		for i in range(0,len(self.params)):
			rnd = random.randrange(0,1)
			listParams.append(listElements[rnd].params[i])
			listValues.append(listElements[rnd].values[i])
		element2 = ElementAlgoGenetique(listParams,listValues,0)
		if random.randrange(0,3) == 0:
			element2 = element2.mutation()
		return element2

class AIgenetique():
	def score(self,statsAgg):
		return 0
	
	def getAI(self,listValues):
		return None

class AlgoGenetique():
	
	def __init__(self,statsAggFactory,aiGenetique,heuristic,nbIterationsMax,nbIndividusMax,ficResults):
		self.elements=[heuristic.mutation()]
		self.statsAggFactory = statsAggFactory
		self.bestElement= heuristic
		self.nbIterations = 0
		self.nbIterationsMax = nbIterationsMax
		self.cptIndividus = 0
		self.nbIndividusMax = nbIndividusMax
		self.ficResults=ficResults
		self.individus = []
		self.heuristic= heuristic
		self.aiGenetique = aiGenetique
	
	def initialisation(self) :
		print("_____Generation_" + str(self.nbIterations) + "______  best : " + str(self.bestElement.fitScore))
		for i in range(len(self.individus),self.nbIndividusMax):
			self.individus.append(self.heuristic.elementAleatoire())

	def eval(self,player):
		statsAgg = self.statsAggFactory.getStatsAgg()
		statsAgg.agg(player)
		#print(statsAgg.line)
		printStatsAggAlgoGen(self.ficResults,statsAgg,self.nbIterations)
		self.individus[self.cptIndividus].fitScore = self.score(statsAgg) 
		if(self.individus[self.cptIndividus].fitScore >= self.bestElement.fitScore):
			self.bestElement = self.individus[self.cptIndividus]
		print(player.nature + " => " + str(self.individus[self.cptIndividus].fitScore))

	def score(self,statsAgg):
		#return statsAgg.avg_round_won
		return self.aiGenetique.score(statsAgg)

	def step(self,player) :
		self.eval(player)
		self.cptIndividus = self.cptIndividus + 1
		if self.cptIndividus == self.nbIndividusMax:
			self.nbIterations =  self.nbIterations + 1
			if self.nbIterations  != self.nbIterationsMax:
				self.croisement()
				self.initialisation()
				self.cptIndividus = 0
	
	def croisement2(self):
		listSelection = [i for i in self.individus if i.fitScore >= self.heuristic.fitScore]
		self.individus = []
		while len(listSelection) > 2 :
			ind = listSelection.pop()
			ind2 = listSelection.pop()
			self.individus.append(ind.croisement(ind2))

	def croisement(self):
		listSelection = [i for i in self.individus if i.fitScore >= self.heuristic.fitScore]
		self.individus = []
		if(len(listSelection) > 2 ):
			for i in range(0,len(listSelection)):
				ind = listSelection[random.randrange(0,len(listSelection))]
				ind2 = listSelection[random.randrange(0,len(listSelection))]
				self.individus.append(ind.croisement(ind2))

	def getAI(self):
		#return AITAFV1(self.individus[self.cptIndividus].values[0],self.individus[self.cptIndividus].values[1],self.individus[self.cptIndividus].values[2])
		return self.aiGenetique.getAI(self.individus[self.cptIndividus].values)

	def getAIHeuristic(self):
		return self.aiGenetique.getAI(self.heuristic.values)

	def isOver(self):
		return self.nbIterations == self.nbIterationsMax


def playersMaker(game,algoAI,AIFactory) :
	listAI = []
	if(algoAI is not None):
		listAI.append(algoAI.getAI())
		for i in range (1,game.game_params["nb_players"]):
			listAI.append(algoAI.getAIHeuristic())
	else :
		for i in range (0,game.game_params["nb_players"]):
			listAI.append(AIFactory.getAI(game.game_params["player" + str(i+1)]["ai"]))
	#print(listAI)
	aiManager = AIManager()
	player = None
	if  listAI[0] is not None : 
		player = PlayerAI(game.game_params["player1"]["name"],listAI[0])
		aiManager.addPlayer(player)
	else :
		player = Player(game.game_params["player1"]["name"])

	game.addPlayer(player)
	
	
	print("nbjoueurs" + str(game.game_params["nb_players"]))
	for i in range (1,game.game_params["nb_players"]):
		playerAI = PlayerAI(game.game_params["player"+ str(i+1)]["name"],listAI[i])
		aiManager.addPlayer(playerAI)
		game.addPlayer(playerAI)

	if(game.game_params["deck"] == "personal"):
		for p in game.players:
			p.cardsOwned = loadCardsOwned(p.name)
			print("OK " + p.name)
			print(p.cardsOwned)	

	return aiManager
		
