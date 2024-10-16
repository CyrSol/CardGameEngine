import tkinter as tk
import pygame
import os, platform
from tkinter import ttk

PYGAME_GAME_PARAM= 25
PYGAME_INPUT = 26

transco_click=[0,1,3,2]
class EventManagerTKform(object):

    def __init__(self):
        self.listeEvents=[]

    def on_click(self,event):
        #print("Position de la souris:", event.x, event.y)
        #print(event)
        self.listeEvents.append(pygame.event.Event(pygame.MOUSEBUTTONUP,{"pos":(event.x, event.y), "button" : transco_click[event.num]}))
        #print(self.listeEvents)

    def key(self,event):
        #print("Touche:", event.keysym, event.keycode)
        if(len(event.keysym) == 1):
            self.listeEvents.append(pygame.event.Event(pygame.KEYDOWN,{"key": ord(event.keysym) }))
        #print(self.listeEvents)

    def game_param(self,key,value):
        #self.listeEvents.append(pygame.event.Event(PYGAME_GAME_PARAM,{"key": key, "value":value }))
        event=pygame.event.Event(pygame.USEREVENT,{"value":value , "key" : key, "type_event" : "param"})
        self.listeEvents.append(event)

    def game_input(self,value):
        #print(value)
        event=pygame.event.Event(pygame.USEREVENT,{"value":value , "type_event" : "input"})
        #event=pygame.event.Event(1024,code="make")
        #print(event)
        self.listeEvents.append(event)

    def game_action(self,keysym):
        self.listeEvents.append(pygame.event.Event(pygame.KEYDOWN,{"key": ord(keysym) }))
        #print("game action => " + keysym)

class MenuAction(object):
    def __init__(self,eventManagerTKform,key):
        self.eventManagerTKform = eventManagerTKform
        self.key = key
    def action(self):
        self.eventManagerTKform.game_action(self.key)

class MenuParam(object):
    def __init__(self,eventManagerTKform,key,value):
        self.eventManagerTKform = eventManagerTKform
        self.key = key
        self.value = value
    def action(self):
        self.eventManagerTKform.game_param(self.key,self.value)


class FormTk(object):

    def __init__(self,game_params):
        self.gameloop = None
        self.root = None
        self.eventManagerTkform= EventManagerTKform()	
        self.mainmenu=  None
        self.iamenu =  None
        self.rulesmenu = None
        self.aboutmenu = None
        self.game_params = game_params
        self.vars = []

    def update(self):
      if self.gameLoop is not None : 
          for dic in self.gameLoop.getOutputMessages():
           #print(dic)
           ret = self.popup(dic)
           #print(ret)
           self.eventManagerTkform.game_input(ret)
          for event in self.eventManagerTkform.listeEvents:
             #print(event)
             pygame.event.post(event)
          self.eventManagerTkform.listeEvents.clear()
          #print(self.gameLoop.gameManager.eventManager.events)
          self.gameLoop.step()
          if (self.gameLoop.done):
             self.root.destroy()
      
     
      #print("update")
      self.root.after(10, self.update)

    def initialisation(self,title,width,height,eventManagerTkform):
        self.eventManagerTkform = eventManagerTkform
        self.root = tk.Tk()
        self.root.title(title)
        self.root.geometry('300x100+50+50')
        # Large Frame
        #win_frame = tk.Frame(self.root, width=width, height=height, highlightbackground='#595959', highlightthickness=2)

        # Menu
        self.mainmenu = tk.Menu(self.root)

        self.filemenu = tk.Menu(self.mainmenu, tearoff=0)
        self.filemenu.add_command(label="Nouvelle partie", command=MenuAction(self.eventManagerTkform,'n').action)
        self.filemenu.add_command(label="Rejouer partie", command=MenuAction(self.eventManagerTkform,'r').action)
        self.filemenu.add_command(label="Sauver paramètres de jeu", command=MenuAction(self.eventManagerTkform,'s').action)

        self.debugmenu = tk.Menu(self.mainmenu, tearoff=0)
        self.debugmenu.add_command(label="Debug", command=MenuAction(self.eventManagerTkform,'d').action)
        self.debugmenu.add_command(label="Pas vers l'avant", command=MenuAction(self.eventManagerTkform,'f').action)
        self.debugmenu.add_command(label="Pas vers l'arrière", command=MenuAction(self.eventManagerTkform,'b').action)

        self.aimenu = tk.Menu(self.mainmenu, tearoff=0)
        self.rulesmenu = tk.Menu(self.mainmenu, tearoff=0)
        self.aboutmenu = tk.Menu(self.mainmenu, tearoff=0)

        self.root.config(menu=self.mainmenu)
        self.mainmenu.add_cascade(label="Fichier",menu=self.filemenu)      
        self.mainmenu.add_cascade(label="Debug",menu=self.debugmenu)    
        self.mainmenu.add_cascade(label="IA",menu=self.aimenu)  
        self.mainmenu.add_cascade(label="Règles",menu=self.rulesmenu)
        self.mainmenu.add_cascade(label="A propos",menu=self.aboutmenu)

        # pygame
        #pygame_frame = tk.Frame(win_frame, width=width, height=height, highlightbackground='#595959', highlightthickness=2)
        #embed = tk.Frame(self.root, width=width, height=height)
        #embed.bind("<Button-1>", self.eventManagerTkform.on_click)
        #embed.bind("<Double-Button-1>", self.eventManagerTkform.on_click)
        #embed.bind("<Button-3>", self.eventManagerTkform.on_click)
        #embed.bind_all("<Key>", self.eventManagerTkform.key)

        # Packing
        #win_frame.pack(expand=False)
        #win_frame.pack_propagate(0)
        #pygame_frame.pack(side="top")
        #embed.pack(side="top")

        #This embeds the pygame window
        #os.environ['SDL_WINDOWID'] = str(self.root.winfo_id())
        #system = platform.system()
        #if system == "Windows":
            #os.environ['SDL_VIDEODRIVER'] = 'windib'
        

        #self.root.update_idletasks()
 
    def popup(self,dic):
        print(dic)
        fInfos = tk.Toplevel()		  # Popup -> Toplevel()
        fInfos.title(dic["title"])
        fInfos.geometry('500x90')
        tk.Label(fInfos, text=dic["text"]).pack(padx=10, pady=10)
        widgetsList = []
        i=0
        #print(dic["value"])
        maxValue = 5
        for key, value in dic["value"].items():
        	for v in value :
        		if maxValue < len(str(v)) :
        			maxValue = len(str(v)) 
        print("size : " + str(maxValue))
        		
        for key, value in dic["value"].items():
              widgetsList.append(self.widget(fInfos,value,i,maxValue))
              i=i+1

        tk.Button(fInfos, text='OK', command=fInfos.destroy).pack(padx=5, pady=5)
        fInfos.transient(self.root) 	  # Réduction popup impossible 
        fInfos.grab_set()		  # Interaction avec fenetre jeu impossible
        self.root.wait_window(fInfos)   # Arrêt script principal
        ret = []
        for w in widgetsList:
            ret.append(self.vars[w.tag].get())
        return ret

    def widget(self, window,values, tag, maxValue):
        self.vars.append(tk.StringVar())
        length = len(values)
        listbox = tk.ttk.Combobox(window)
        listbox.config(textvariable = self.vars[tag], state = "readonly", values = values, width=maxValue)
        listbox.current(0) # index of values for current table
        listbox.pack(padx=1, pady=1)
        listbox.tag = tag
        return listbox


