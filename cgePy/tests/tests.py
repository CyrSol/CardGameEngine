import cgePy

def main() :
    print(dir(cgePy))
    card = cgePy.card_game.Card("xx",1,2,2,2)
    print(card.getInfo())
    

if __name__ == '__main__':
	main()