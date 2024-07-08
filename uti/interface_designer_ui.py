import pygame
import sys, os
import tkinter as tk
from tkinter import ttk
from cgePy.card_game import loadParams
import threading

WHITE = (255,255,255)

class FakeDeck(object):

       def __init__(self,r,int1,int2,nb,v,name,hollow,nbmax):
          self.r = r
          self.int1 = int1
          self.int2 = int2
          self.nb = nb
          self.v = v
          self.name= name
          self.hollow=hollow
          self.nbmax=nbmax

       def draw(self,screen,c):
          
           for i in range(0,self.nb):
             x=self.r.x
             y=self.r.y
             a, b = divmod(i, self.nbmax) 
             if(not self.v):
                  y=y+(a*self.r.height)+self.int2*a
             else:
                  x=x+(a*self.r.width)+self.int2*a
              
             if(not self.v):
               x=x+(b*self.r.width/self.int1)+self.int2*b
             else:
               y=y+(b*self.r.height/self.int1)+self.int2*b
             #print(str(x)+ ":" + str(y) + ":" + str(a) + ":" + str(b))
             rect = pygame.Rect(x,y,self.r.width,self.r.height)
             pygame.draw.rect(screen, c, rect) #delete old
             pygame.display.update(rect)

       def to_string(self):
          orientation=""
          hollow=""
          if self.v : orientation = "v" 
          else : orientation = "h" 
          if self.hollow : hollow = "h" 
          else : hollow = "x" 
          return self.name + ";" + str(self.r.x) + ";" + str(self.r.y) + ";" + str(self.r.width) + ";" + str(self.r.height) + ";" + str(self.int1) + ";" + str(self.int2) + ";" + orientation + ";" + hollow + ";" + str(self.nbmax)

       def from_string(line):
          elements = line.split(";")
          r = pygame.Rect(int(elements[1]),int(elements[2]),int(elements[3]),int(elements[4]))
          int1 = int(elements[5])
          int2 = int(elements[6])
          nb = int(elements[9])
          v =  True if elements[7] == "v" else False
          name= elements[0]
          hollow= True if elements[8] == "h" else False
          nbmax=int(elements[9])

          return FakeDeck(r,int1,int2,nb,v,name,hollow,nbmax)


class FakeUIElement(object):

       def __init__(self,r,var,font,size,v,re,g,b,typele,interval,text=""):
         self.var=var
         self.font=font
         self.size=size
         self.v = v
         self.r=r
         self.re=re
         self.g=g
         self.b=b
         self.interval=interval
         self.typele=typele
         self.nb = 3 if typele == "liste" else 1
         self.text = text if text != "" else "X"

       def draw(self,screen):
           c = (self.re,self.g,self.b)
           for i in range(0,self.nb):
             x=self.r.x
             y=self.r.y
             
             if(self.v):
                  y=y+(i*self.r.height)+self.interval*i
             else:
                  x=x+(i*self.r.width)+self.interval*i
              
             #print(str(x)+ ":" + str(y) + ":" + str(a) + ":" + str(b))
             font = pygame.font.SysFont(self.font,self.size)
             text = font.render(self.text if self.typele != "constante"else self.var,True,c)
             screen.blit(text,[x,y])
             #rect = pygame.Rect(x,y,self.r.width,self.r.height)
             #pygame.draw.rect(screen, c, rect) #delete old
             #pygame.display.update(rect)


       def to_string(self):
          orientation=""
          hollow=""
          if self.v : orientation = "v" 
          else : orientation = "h" 
          
          return self.var + ";" + self.font + ";" + str(self.size) + ";" + orientation + ";" + str(self.r.x) + ";" + str(self.r.y) + ";" + str(self.r.width) + ";" + str(self.r.height) + ";" + str(self.re) + ";" + str(self.g) + ";" + str(self.b) + ";"  + self.typele  + ";" + str(self.interval)

       def from_string(line):
          elements = line.split(";")
          r = pygame.Rect(int(elements[4]),int(elements[5]),int(elements[6]),int(elements[7]))
          var= elements[0]
          font = elements[1]
          size = int(elements[2])
          v =  True if elements[3] == "v" else False
          re = int(elements[8])
          g=int(elements[9])
          b=int(elements[10])
          typele= elements[11]
          interval=int(elements[12])

          return FakeUIElement(r,var,font,size,v,re,g,b,typele,interval)

b_save = False
b_load = False
b_delete = False
b_unselect = False
b_update = False

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

def update():
    global b_update
    b_update = True

def save_file(file_name, decks):
   basePath = os.getcwd()
   #file_name = "config/"+file_name
   file_absolute_name= os.path.join(basePath,file_name)
   print(file_absolute_name)
   fic = open(file_absolute_name,'w')
   for d in decks:
      fic.write(d.to_string() + '\n')
   fic.close

def load_file(file_name):
   basePath = os.getcwd()
   #file_name = "config/"+file_name
   file_absolute_name= os.path.join(basePath,file_name)
   print(file_absolute_name)
   fic = open(file_absolute_name,'r')
   decks = []
   for line in fic.readlines():
      d = FakeDeck.from_string(line)
      print(d.to_string())
      decks.append(d)
   fic.close
   return decks

def load_file_uie(file_name):
   basePath = os.getcwd()
   #file_name = "config/"+file_name
   file_absolute_name= os.path.join(basePath,file_name)
   print(file_absolute_name)
   fic = open(file_absolute_name,'r')
   decks = []
   for line in fic.readlines():
      d = FakeUIElement.from_string(line)
      print(d.to_string())
      decks.append(d)
   fic.close
   return decks

general_params = loadParams("general_params.json")
game_params = loadParams(general_params["game_params"])
pygame.init()
pygame.key.set_repeat(300, 30)
width = general_params["screen_width"]
menu_width = 200
height = general_params["screen_height"] + 10
screen = pygame.display.set_mode((width, height))
img = None
picture = None
imagePathBack = general_params["background"]
img = pygame.image.load(imagePathBack).convert()
picture = pygame.transform.scale(img, (width, height-15))

screen.fill((255, 255, 255))
if img is not None:
    screen.blit(picture, [0, 0])

clock = pygame.time.Clock()

root = tk.Tk()
root.title("Interface de Création de Jeu")

frame = tk.Frame(root, width=menu_width, height=height+100)
frame.pack(side=tk.LEFT)

menu_frame = tk.Frame(frame, width=menu_width, height=height+100, bg='black')
menu_frame.pack_propagate(False)
menu_frame.pack(side=tk.RIGHT, fill=tk.Y)

fileName = tk.Entry(menu_frame)
fileName.insert(0, general_params["fic_interface"])
fileName.pack(pady=5)
nbPlayers = tk.Entry(menu_frame)
nbPlayers.insert(0, str(game_params["nb_players"]))
nbPlayers.pack(pady=5)
e_counter_font = tk.Entry(menu_frame)
e_counter_font.insert(0, "arial")
e_counter_font.pack(pady=5)
e_counter_var = tk.Entry(menu_frame)
e_counter_var.insert(0, "var")
e_counter_var.pack(pady=5)
e_counter_text = tk.Entry(menu_frame)
e_counter_text.insert(0, "XXXX")
e_counter_text.pack(pady=5)
size_label = tk.Label(menu_frame, text="Size")
size_label.pack(pady=5)
size_slider_var = tk.IntVar(value=1)
size_slider = tk.Scale(menu_frame, from_=0, to=75, orient=tk.HORIZONTAL, variable=size_slider_var)
size_slider.pack(pady=5)
checker_v_var = tk.BooleanVar()
checker_v = tk.Checkbutton(menu_frame, text="Vertical", variable=checker_v_var)
checker_v.pack(pady=5)
sliders = tk.Scale(menu_frame, from_=0, to=75, orient=tk.HORIZONTAL, label="S")
sliders.pack(pady=5)
sliderr = tk.Scale(menu_frame, from_=0, to=255, orient=tk.HORIZONTAL, label="R")
sliderr.pack(pady=5)
sliderg = tk.Scale(menu_frame, from_=0, to=255, orient=tk.HORIZONTAL, label="G")
sliderg.pack(pady=5)
sliderb = tk.Scale(menu_frame, from_=0, to=255, orient=tk.HORIZONTAL, label="B")
sliderb.pack(pady=5)
sliderInt = tk.Scale(menu_frame, from_=0, to=50, orient=tk.HORIZONTAL, label="Interval")
sliderInt.pack(pady=5)
e_counter_type = tk.Entry(menu_frame)
e_counter_type.insert(0, "element")
e_counter_type.pack(pady=5)

button_save = tk.Button(menu_frame, text="Save", command=save)
button_save.pack(pady=5)
button_load = tk.Button(menu_frame, text="Load", command=load)
button_load.pack(pady=5)
button_delete = tk.Button(menu_frame, text="Delete", command=delete)
button_delete.pack(pady=5)
button_unselect = tk.Button(menu_frame, text="Unselect", command=unselect)
button_unselect.pack(pady=5)
button_update = tk.Button(menu_frame, text="Update", command=update)
button_update.pack(pady=5)

embed = tk.Frame(root, width=menu_width, height=height)
embed.pack()
#os.environ['SDL_WINDOWID'] = str(embed.winfo_id())
#os.environ['SDL_VIDEODRIVER'] = 'x11'

pygame.key.set_repeat(300, 30)
pygame.display.init()

nbPlayersText = ""
if general_params["multi_fic_config"]:
    nbPlayersText = nbPlayers.get()
deck_liste = load_file(fileName.get()+nbPlayersText+general_params["extension_fic_config"])
uie_liste = load_file_uie(fileName.get()+nbPlayersText+general_params["extension_fic_interface"])

def getUIElement(x, y):
    var = e_counter_var.get()
    font = e_counter_font.get()
    size = int(sliders.get())
    v = int(checker_v_var.get())
    re = int(sliderr.get())
    g = int(sliderg.get())
    b = int(sliderb.get())
    typele = e_counter_type.get()
    interval = int(sliderInt.get())
    text = e_counter_text.get()
    fonte = pygame.font.SysFont(font, size)
    text_width, text_height = fonte.size(text)
    rectangle = pygame.Rect(x, y, text_width, text_height)
    return FakeUIElement(rectangle, var, font, size, v, re, g, b, typele, interval, text)

rect = pygame.Rect(width, 0, 2, height)
pygame.draw.rect(screen, (0, 0, 0), rect)
pygame.display.update(rect)

rect = pygame.Rect(width/2, 0, 2, height)
pygame.draw.rect(screen, (0, 0, 0), rect)
pygame.display.update(rect)

rect = pygame.Rect(0, height/2, width, 2)
pygame.draw.rect(screen, (0, 0, 0), rect)
pygame.display.update(rect)

rect = pygame.Rect(0, height-15, width, 2)
pygame.draw.rect(screen, (0, 0, 0), rect)
pygame.display.update(rect)

change = True
playing_game = True
selected_uie = None

def mainloop():
    global change, selected_deck, b_unselect, b_delete, b_save, b_load, deck_liste, playing_game, b_update, selected_uie, uie_liste, root
    while playing_game:
        moved = False
        m_x = 0
        m_y = 0
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                playing_game = False
                root.quit()
                break
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
                current_uie = None
                if selected_uie is None:
                    for d in reversed(uie_liste):
                        if(d.r.collidepoint(pos[0], pos[1])):
                            current_uie = d
                            selected_uie = d
                            e_counter_var.delete(0, tk.END)
                            e_counter_var.insert(0,d.var)
                            e_counter_font.delete(0, tk.END)
                            e_counter_font.insert(0,d.font)
                            sliders.set((d.size))
                            checker_v_var.set((d.v))
                            sliderr.set((d.re))
                            sliderg.set((d.g))
                            sliderb.set((d.b))
                            e_counter_type.delete(0, tk.END)
                            e_counter_type.insert(0,d.typele)
                            sliderInt.set((d.interval))
                            e_counter_text.delete(0, tk.END)
                            e_counter_text.insert(0,d.text)
                            change = True
                            break
                if(current_uie is None):
                    uie_liste.append(getUIElement(pos[0], pos[1]))
                    change = True
        if(b_load or b_save):
            nbPlayersText = ""
            if general_params["multi_fic_config"]:
                nbPlayersText = nbPlayers.get()
        if(b_unselect):
            b_unselect = False
            selected_uie = None
            change = True
        if(b_delete and selected_uie is not None):
            b_delete = False
            uie_liste.remove(selected_uie)
            selected_uie = None
            change = True
        if(b_save):
            b_save = False
            save_file(fileName.get()+nbPlayersText+general_params["extension_fic_interface"], uie_liste)
            save_file(fileName.get()+nbPlayersText+general_params["extension_fic_config"], deck_liste)
        if(b_load):
            b_load = False
            deck_liste = load_file(fileName.get()+nbPlayersText+general_params["extension_fic_config"])
            uie_liste = load_file_uie(fileName.get()+nbPlayersText+general_params["extension_fic_interface"])
            selected_uie = None
            change = True
        if(moved and selected_uie is not None):
            if(m_x != 0 or m_y != 0):
                selected_uie.r.y = selected_uie.r.y + m_y
                selected_uie.r.x = selected_uie.r.x + m_x
                change = True
        if(change):
            change = False
            screen.fill((255, 255, 255))
            if img is not None:
                screen.blit(picture, [0, 0])
            rect = pygame.Rect(width, 0, 2, height)
            pygame.draw.rect(screen, (0, 0, 0), rect)
            rect = pygame.Rect(width/2, 0, 2, height)
            pygame.draw.rect(screen, (0, 0, 0), rect)
            rect = pygame.Rect(0, height/2, width, 2)
            pygame.draw.rect(screen, (0, 0, 0), rect)
            rect = pygame.Rect(0, height-15, width, 2)
            pygame.draw.rect(screen, (0, 0, 0), rect)
            
            font = pygame.font.Font(None,20)
            for d in deck_liste:
               c = (0,100,100) if d == selected_uie else (0,0,0)
               d.draw(screen,c) 
               text = font.render(d.name,True,WHITE)
               screen.blit(text,[d.r.x,d.r.y])
            if selected_uie is not None:
               pygame.draw.rect(screen, (0,100,100), selected_uie.r)
          
            for uie in uie_liste:
                uie.draw(screen)
            pygame.display.flip()
            
        clock.tick(30)
        #root.after(100, start_pygame_threads)
        
def start_pygame_thread():
    threading.Thread(target=mainloop).start()

root.after(100, start_pygame_thread)
root.mainloop()
pygame.quit()

