import ui4cgePy 
from ui4cgePy import card_display
from cgePy.card_manager import loadParams,loadCards

def main():
	print(dir(ui4cgePy))
	general_params=loadParams("general_params.json")
	card_display.debug_display_cards(general_params,loadCards)
	
if __name__ == '__main__':
	main()