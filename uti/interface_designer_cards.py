import os
import pygame
import tkinter as tk
from tkinter import ttk
from cgePy.card_game import loadParams

WHITE = (255, 255, 255)
BLACK = (0, 0, 0)

class FakeDeck:
    def __init__(self, r, int1, int2, nb, v, name, hollow, nbmax):
        self.r = r
        self.int1 = int1
        self.int2 = int2
        self.nb = nb
        self.v = v
        self.name = name
        self.hollow = hollow
        self.nbmax = nbmax

    def draw(self, screen, c):
        for i in range(0, self.nb):
            x = self.r.x
            y = self.r.y
            a, b = divmod(i, self.nbmax)
            if not self.v:
                y += (a * self.r.height) + self.int2 * a
            else:
                x += (a * self.r.width) + self.int2 * a

            if not self.v:
                x += (b * self.r.width / self.int1) + self.int2 * b
            else:
                y += (b * self.r.height / self.int1) + self.int2 * b

            rect = pygame.Rect(x, y, self.r.width, self.r.height)
            pygame.draw.rect(screen, c, rect)
            rect = pygame.Rect(width/2, 0, 2, height)
            pygame.draw.rect(screen, (0, 0, 0), rect)
            rect = pygame.Rect(0, height/2, width, 2)
            pygame.draw.rect(screen, (0, 0, 0), rect)
            pygame.display.update(rect)

    def to_string(self):
        orientation = "v" if self.v else "h"
        hollow = "h" if self.hollow else "x"
        return f"{self.name};{self.r.x};{self.r.y};{self.r.width};{self.r.height};{self.int1};{self.int2};{orientation};{hollow};{self.nbmax}"

    @staticmethod
    def from_string(line):
        elements = line.split(";")
        r = pygame.Rect(int(elements[1]), int(elements[2]), int(elements[3]), int(elements[4]))
        int1 = int(elements[5])
        int2 = int(elements[6])
        nb = int(elements[9])
        v = elements[7] == "v"
        name = elements[0]
        hollow = elements[8] == "h"
        nbmax = int(elements[9])
        return FakeDeck(r, int1, int2, nb, v, name, hollow, nbmax)

b_save = False
b_load = False
b_delete = False
b_unselect = False

def save():
    global b_save
    b_save = True

def load():
    global b_load
    b_load = True

def delete():
    global b_delete
    b_delete = True

def unselect():
    global b_unselect
    b_unselect = True

def save_file(file_name, decks):
    base_path = os.getcwd()
    file_absolute_name = os.path.join(base_path, file_name)
    with open(file_absolute_name, 'w') as fic:
        for d in decks:
            fic.write(d.to_string() + '\n')

def load_file(file_name):
    base_path = os.getcwd()
    file_absolute_name = os.path.join(base_path, file_name)
    decks = []
    with open(file_absolute_name, 'r') as fic:
        for line in fic.readlines():
            d = FakeDeck.from_string(line)
            decks.append(d)
    return decks

general_params = loadParams("config/general_params.json")

# Initialisation de pygame
pygame.init()
pygame.key.set_repeat(300, 30)
width = general_params["screen_width"]
menu_width = 150
height = general_params["screen_height"] + 10

screen = pygame.display.set_mode((width, height))
# Chargement de l'image de fond
background_path = general_params["background"]

# Configuration de l'interface tkinter
root = tk.Tk()
root.title("Interface de Création de Jeu")

# Frame pour le canvas pygame
frame = tk.Frame(root, width=menu_width, height=height)
frame.pack(side=tk.LEFT)

# Frame pour le menu tkinter
menu_frame = tk.Frame(root, width=menu_width, height=height, bg='gray')
menu_frame.pack_propagate(False)
menu_frame.pack(side=tk.RIGHT, fill=tk.Y)

# Création des widgets tkinter
entry_deckname = tk.Entry(menu_frame)
entry_deckname.insert(0, "player")
entry_deckname.pack(pady=5)
tk.Label(menu_frame, text="Paramètres de Carte").pack(pady=10)
slider_width = tk.Scale(menu_frame, label="Largeur", from_=0, to=200, orient='horizontal')
slider_width.set(general_params["card_width"])
slider_width.pack(pady=5)
slider_height = tk.Scale(menu_frame, label="Hauteur", from_=0, to=200, orient='horizontal')
slider_height.set(general_params["card_height"])
slider_height.pack(pady=5)
slider_interval = tk.Scale(menu_frame, label="Interval", from_=1, to=8, orient='horizontal')
slider_interval.pack(pady=5)
slider_interval2 = tk.Scale(menu_frame, label="Interval2", from_=1, to=20, orient='horizontal')
slider_interval2.pack(pady=5)
slider_nb_cards = tk.Scale(menu_frame, label="Nombre de Cartes", from_=1, to=20, orient='horizontal')
slider_nb_cards.pack(pady=5)

vertical_var = tk.BooleanVar()
checkbox_vertical = tk.Checkbutton(menu_frame, text="Vertical", variable=vertical_var)
checkbox_vertical.pack(pady=5)

hollow_var = tk.BooleanVar()
checkbox_hollow = tk.Checkbutton(menu_frame, text="Hollow", variable=hollow_var)
checkbox_hollow.pack(pady=5)

slider_nb_max = tk.Scale(menu_frame, label="Nombre Max", from_=1, to=20, orient='horizontal')
slider_nb_max.pack(pady=5)
entry_name = tk.Entry(menu_frame)
entry_name.insert(0, general_params["fic"])
entry_name.pack(pady=5)
entry_num = tk.Entry(menu_frame)
entry_num.insert(0, "")
entry_num.pack(pady=5)

# Boutons tkinter
tk.Button(menu_frame, text="Sauvegarder", command=save).pack(pady=10)
tk.Button(menu_frame, text="Charger", command=load).pack(pady=5)
tk.Button(menu_frame, text="Supprimer", command=delete).pack(pady=5)
tk.Button(menu_frame, text="Désélectionner", command=unselect).pack(pady=5)

# Initialisation du canvas pygame
embed = tk.Frame(frame, width=menu_width, height=height)  # Frame to hold the pygame window
embed.pack()
#os.environ['SDL_VIDEODRIVER'] = 'x11'
#os.environ['SDL_WINDOWID'] = str(embed.winfo_id())

pygame.display.set_caption("Interface de Création de Jeu")
pygame.display.init()
img = pygame.image.load(background_path).convert()
picture = pygame.transform.scale(img, (width, height - 15))

# Liste des decks
deck_list = []

clock = pygame.time.Clock()
selected_deck = None
change = False

# Boucle principale
def mainloop():
    global change, selected_deck, b_unselect, b_delete, b_save, b_load, deck_list
    moved = False
    m_x = 0
    m_y = 0
    for event in pygame.event.get():

        if event.type == pygame.QUIT:
            root.quit()
            return
        elif event.type == pygame.KEYDOWN:
                if event.key == pygame.K_ESCAPE: unselect()
                elif event.key == pygame.K_x: delete()
                elif event.key == pygame.K_DOWN: 
                    moved = True
                    m_y = 1 
                elif event.key == pygame.K_UP: 
                    moved = True
                    m_y = -1 
                elif event.key == pygame.K_RIGHT: 
                    moved = True
                    m_x = 1 
                elif event.key == pygame.K_LEFT: 
                    moved = True
                    m_x = -1 
        elif event.type == pygame.MOUSEBUTTONUP:
            pos = pygame.mouse.get_pos()
            current_deck = None
            if selected_deck is None:
                for d in reversed(deck_list):
                    if d.r.collidepoint(pos):
                        current_deck = d
                        selected_deck = d
                        slider_interval.set(current_deck.int1)
                        slider_interval2.set(current_deck.int2)
                        slider_width.set(current_deck.r.width)
                        slider_height.set(current_deck.r.height)
                        slider_nb_cards.set(current_deck.nb)
                        vertical_var.set(current_deck.v)
                        entry_deckname.delete(0, tk.END)
                        entry_deckname.insert(0, current_deck.name)
                        hollow_var.set(current_deck.hollow)
                        slider_nb_max.set(current_deck.nbmax)
                        change = True
                        continue

            x = pos[0] #- slider_width.get() / 2
            y = pos[1] #- slider_height.get() / 2
            if current_deck is None and x < width - slider_width.get() and slider_width.get() > 0 and slider_height.get() > 0:
                rectangle = pygame.Rect(x, y, slider_width.get(), slider_height.get())
                deck = FakeDeck(rectangle, slider_interval.get(), slider_interval2.get(), slider_nb_cards.get(), vertical_var.get(), entry_deckname.get(), hollow_var.get(), slider_nb_max.get())
                if selected_deck is not None:
                    deck_list[deck_list.index(selected_deck)] = deck
                    selected_deck = None
                else:
                    deck_list.append(deck)
                print(deck.to_string())
                change = True

    if b_unselect:
        selected_deck = None
        change = True
        b_unselect = False

    if b_delete:
        if selected_deck is not None:
            deck_list.remove(selected_deck)
            selected_deck = None
            change = True
        b_delete = False

    if b_save:
        save_file(general_params["fic_config_folder"] + entry_name.get() + entry_num.get() + general_params["extension_fic_config"], deck_list)
        b_save = False

    if b_load:
        deck_list = load_file(general_params["fic_config_folder"] + entry_name.get() + entry_num.get() +  general_params["extension_fic_config"])
        b_load = False
        change = True

    if(moved and selected_deck is not None):
            if(m_x != 0 or m_y != 0):
                selected_deck.r.y = selected_deck.r.y + m_y
                selected_deck.r.x = selected_deck.r.x + m_x
                change = True
    if change:
        if img:
            screen.blit(picture, [0, 0])
        else:
            screen.fill(WHITE)

        for d in deck_list:
            c = (255, 0, 0) if d == selected_deck else (0, 255, 0)
            d.draw(screen, c)
            font = pygame.font.Font(None, 20)
            text = font.render(d.name, True, WHITE)
            screen.blit(text, [d.r.x, d.r.y])
        pygame.display.flip()
        change = False

    clock.tick(60)
    root.after(10, mainloop)

root.after(10, mainloop)
root.mainloop()

pygame.quit()

