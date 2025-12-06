import pygame
import tkinter as tk
from tkinter import filedialog, simpledialog, ttk
import json
import os

# --- Initialisation Pygame ---
pygame.init()
SCREEN_W, SCREEN_H = 600, 800
screen = pygame.display.set_mode((SCREEN_W, SCREEN_H))
pygame.display.set_caption("Card Editor Prototype")
clock = pygame.time.Clock()

# --- Motifs (dictionnaire nom -> image) ---
motifs_dict = {}
motifs_folder = "motifs"  # dossier contenant les PNG de motifs
for f in os.listdir(motifs_folder):
    if f.endswith(".png"):
        name = os.path.splitext(f)[0]
        motifs_dict[name] = pygame.image.load(os.path.join(motifs_folder,f)).convert_alpha()

# --- Classes ---
class Layer:
    def __init__(self, width, height, name="Layer", image=None):
        self.width = width
        self.height = height
        self.name = name
        self.image = image
        self.items = []  # objets à placer sur la couche (motifs ou images)

    def draw(self, surface):
        if self.image:
            surface.blit(self.image, (0,0))
        for item in self.items:
            item.draw(surface)

class PatternItem:
    def __init__(self, surface, pos=(0,0), name=None):
        self.surface = surface
        self.pos = pos
        self.name = name  # pour sauvegarde JSON

    def draw(self, surface):
        surface.blit(self.surface, self.pos)

    def contains(self, pos):
        x, y = self.pos
        w, h = self.surface.get_size()
        return x <= pos[0] <= x+w and y <= pos[1] <= y+h

class CardPattern:
    def __init__(self, width=400, height=600):
        self.width = width
        self.height = height
        self.layers = [
            Layer(width,height,name="Background"),
            Layer(width,height,name="Image Layer"),
            Layer(width,height,name="Motifs")
        ]

    def draw(self, surface):
        for layer in self.layers:
            layer.draw(surface)

    def add_motif(self, motif_name, pos):
        if motif_name in motifs_dict:
            item = PatternItem(motifs_dict[motif_name], pos, name=motif_name)
            self.layers[2].items.append(item)

    def to_json(self):
        data = {
            "width": self.width,
            "height": self.height,
            "layers":[]
        }
        for layer in self.layers:
            layer_data = {"name": layer.name, "items":[]}
            for item in layer.items:
                layer_data["items"].append({
                    "name": getattr(item,"name",None),
                    "position": list(item.pos)
                })
            data["layers"].append(layer_data)
        return data

    def save_pattern(self, filename):
        with open(filename, "w") as f:
            json.dump(self.to_json(), f, indent=4)

    def load_pattern(self, filename):
        with open(filename,"r") as f:
            data = json.load(f)
        self.width = data["width"]
        self.height = data["height"]
        self.layers = [Layer(self.width,self.height,name=layer["name"]) for layer in data["layers"]]
        for li, layer_data in enumerate(data["layers"]):
            for item_data in layer_data["items"]:
                name = item_data["name"]
                pos = tuple(item_data["position"])
                if name in motifs_dict:
                    self.layers[li].items.append(PatternItem(motifs_dict[name], pos, name=name))

# --- Tkinter interface ---
root = tk.Tk()
root.title("Pattern Card Editor")

pattern = CardPattern()

selected_motif = tk.StringVar(value=list(motifs_dict.keys())[0])

# --- Callbacks ---
def choose_motif():
    motif = simpledialog.askstring("Motif", "Entrez le nom du motif existant :")
    if motif in motifs_dict:
        selected_motif.set(motif)

def add_motif_to_card():
    x = simpledialog.askinteger("X","Position X:")
    y = simpledialog.askinteger("Y","Position Y:")
    pattern.add_motif(selected_motif.get(), (x,y))

def save_pattern():
    filename = filedialog.asksaveasfilename(defaultextension=".json")
    if filename:
        pattern.save_pattern(filename)
        print(f"Pattern saved to {filename}")

def load_pattern():
    filename = filedialog.askopenfilename(filetypes=[("JSON files","*.json")])
    if filename:
        pattern.load_pattern(filename)
        print(f"Pattern loaded from {filename}")

def export_card():
    surface = pygame.Surface((pattern.width, pattern.height))
    pattern.draw(surface)
    filename = filedialog.asksaveasfilename(defaultextension=".png")
    if filename:
        pygame.image.save(surface, filename)
        print(f"Card exported as {filename}")

# --- Widgets ---
tk.Label(root, text="Motif").pack()
tk.ttk.Combobox(root, textvariable=selected_motif, values=list(motifs_dict.keys())).pack()
tk.Button(root, text="Ajouter motif", command=add_motif_to_card).pack(pady=2)
tk.Button(root, text="Charger pattern", command=load_pattern).pack(pady=2)
tk.Button(root, text="Sauvegarder pattern", command=save_pattern).pack(pady=2)
tk.Button(root, text="Exporter carte PNG", command=export_card).pack(pady=5)

# --- Pygame + Tkinter loop ---
def tk_pygame_loop():
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            root.quit()
            pygame.quit()
            return
    screen.fill((200,200,200))
    pattern.draw(screen)
    pygame.display.flip()
    root.after(50, tk_pygame_loop)

root.after(50, tk_pygame_loop)
root.mainloop()
