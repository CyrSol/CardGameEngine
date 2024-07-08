import ui4cgePy 
from ui4cgePy import card_display
from cgePy.card_manager import loadParams,loadCards

def main():
	print(dir(ui4cgePy))
	general_params=loadParams("general_params.json")
	game_params=loadParams(general_params["game_params"])
	card_display.debug_display_cards(loadCards)
	
if __name__ == '__main__':
	main()