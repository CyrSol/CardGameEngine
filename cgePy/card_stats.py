import sys
import os
import io

class Stats():

	def __init__(self,score=0,round_won=0,round_played=0,game_won=0,game_played=0):
		self.score=score
		self.round_won=round_won
		self.round_played=round_played
		self.game_won=game_won
		self.game_played=game_played


class StatsAggFactory():

	def getHeader(self):
		return "player;nature;nbGamePlayed;nbGameWon;avgScore;avgRoundPlayed;AvgRoundWon"
	def getStatsAgg(self):
		return StatsAgg()

class StatsAgg():
	def __init__(self):
		self.score=0
		self.round_won=0
		self.round_played=0
		self.game_won=0
		self.game_played=0
		self.cpt = 0
		self.avg_score = 0
		self.avg_round_played = 0
		self.avg_round_won = 0
		self.line = ""

	def agg(self,player) :
		stats = player.stats
		self.cpt = len(stats)
		for stat in stats:
			self.score=self.score+stat.score
			self.round_won=self.round_won+stat.round_won
			self.round_played=self.round_played+stat.round_played
			self.game_won=self.game_won+stat.game_won
			self.game_played=self.game_played+stat.game_played
		self.avg_score = self.score/self.game_played
		self.avg_round_played = self.round_played/self.game_played
		self.avg_round_won = self.round_won/self.round_played
		self.line = player.name + ";" + player.nature + ";" + str(self.game_played) + ';' + str(self.game_won)+ ';' + str(self.avg_score) + ';' + str(self.avg_round_played) + ";" + str(self.avg_round_won) 


def printStats(ficName,players,statsAggFactory):
	fic = open(ficName,"w")
	fic.write(statsAggFactory.getHeader() + '\n')
	fic.close()
	for pl in players:
		statsAgg = statsAggFactory.getStatsAgg()
		statsAgg.agg(pl)
		printStatsAgg(ficName,statsAgg)
	

def printStatsAgg(ficName,statsAgg):
	fic = open(ficName,"a")
	line = statsAgg.line
	fic.write(line+'\n')
	fic.close()


def printStatsAggAlgoGen(ficName,statsAgg,numGen):
	fic = open(ficName,"a")
	line = str(numGen) + ";" + statsAgg.line
	fic.write(line+'\n')
	fic.close()
