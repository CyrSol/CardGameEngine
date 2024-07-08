import pygame
import sys
from cgePy.card_manager import *

from ui4cgePy.formTk import *

class GameWindowTK() :

	def display(general_params,game_params,GameManagerFactoryList,transitionManager=None,game_options=None):
		formTk = FormTk(game_params)
		formTk.initialisation(general_params["title"],general_params["screen_width"],general_params["screen_height"]+10,EventManagerTKform())
		screen = pygame.display.set_mode([general_params["screen_width"],general_params["screen_height"]])
		card_dict = loadCardsDict(general_params["cards_dict"],general_params["back_name"])
		pygame.init()
		pygame.font.init()
		#uiManager = uiManagerFactory.getUIManager(general_params["screen_width"],general_params["screen_height"])
		gameLoop = GameLoop(general_params,game_params,GameManagerFactoryList,transitionManager,game_options)
		gameLoop.initialisation(screen,card_dict)
		if  not game_params["benchmarkAI"]  and not game_params["fullAI"]  :
			formTk.gameLoop = gameLoop
			formTk.update()
			formTk.root.mainloop()
			#while(gameLoop.done == False):formTk.update()
		else:
			gameLoop.loop(screen,card_dict)
		
