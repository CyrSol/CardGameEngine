"""
card_template_editor_v2.py

Éditeur de templates de cartes (Option B: Tkinter Canvas) — version améliorée
- projets (dossier avec config.json, templates/, assets/)
- collection de templates dans un projet
- gestion d'assets (import d'images)
- drag & drop d'éléments (texte / image / rect / circle)
- panneau de propriétés (modification des champs CSV attendus)
- undo / redo
- export CSV (1 ligne = 1 élément)
- génération de deck basée sur un CSV `nom_carte;rank;suit;value;tag`
- taille de carte configurable par projet (config.json)
- UI: panneau projet permettant d'éditer card_width / card_height

Usage:
    python card_template_editor_v2.py

Dépendances:
    - Python 3.8+
    - Pillow (pip install pillow)
"""
import os
import json
import csv
import shutil
import re
import random
import tkinter as tk
from tkinter import filedialog, messagebox, simpledialog, colorchooser
from tkinter import ttk
import tkinter.font as tkfont
from PIL import Image, ImageTk, ImageOps, ImageFont, ImageDraw
from dataclasses import dataclass, asdict, field
from typing import List, Optional, Dict

# ---------- Data classes ----------

@dataclass
class TemplateElement:
    type: str = 'text'            # text | image | rect | circle
    value: str = ''               # text content or image path
    x: int = 20
    y: int = 20
    w: Optional[int] = None
    h: Optional[int] = None
    font: str = 'Arial'
    size: int = 24
    color: str = '#000000'
    anchor: str = 'topleft'
    rotate: float = 0.0
    pin: str = 'L'                # L | C | R (Left | Center | Right)

    def to_csv_row(self):
        return [self.type, self.value, str(self.x), str(self.y), str(self.w or ''), str(self.h or ''), self.font, str(self.size), self.color, self.anchor, str(self.rotate), self.pin]

    @staticmethod
    def from_csv_row(row: List[str]):
        return TemplateElement(
            type=row[0] if len(row)>0 else 'text',
            value=row[1] if len(row)>1 else '',
            x=int(row[2]) if len(row)>2 and row[2] else 0,
            y=int(row[3]) if len(row)>3 and row[3] else 0,
            w=int(row[4]) if len(row)>4 and row[4] else None,
            h=int(row[5]) if len(row)>5 and row[5] else None,
            font=row[6] if len(row)>6 else 'Arial',
            size=int(row[7]) if len(row)>7 and row[7] else 24,
            color=row[8] if len(row)>8 and row[8] else '#000000',
            anchor=row[9] if len(row)>9 and row[9] else 'topleft',
            rotate=float(row[10]) if len(row)>10 and row[10] else 0.0,
            pin=row[11] if len(row)>11 and row[11] else 'L'
        )

@dataclass
class Template:
    name: str
    elements: List[TemplateElement] = field(default_factory=list)
    perimeter: str = "all"

    def save_csv(self, path: str):
        with open(path, 'w', newline='', encoding='utf-8') as f:
            writer = csv.writer(f)
            writer.writerow(['type','value','x','y','w','h','font','size','color','anchor','rotate','pin'])
            for e in self.elements:
                writer.writerow(e.to_csv_row())

    @staticmethod
    def load_csv(path: str):
        elements = []
        with open(path, newline='', encoding='utf-8') as f:
            reader = csv.reader(f)
            header = next(reader, None)
            for row in reader:
                if not row:
                    continue
                elements.append(TemplateElement.from_csv_row(row))
        name = os.path.splitext(os.path.basename(path))[0]
        return Template(name=name, elements=elements)

@dataclass
class Project:
    path: str
    name: str
    templates: Dict[str, Template] = field(default_factory=dict)
    assets: Dict[str, str] = field(default_factory=dict)
    assets_dir: str = 'assets'
    card_width: int = 120
    card_height: int = 160

    @staticmethod
    def create(path: str, name: str, card_width: int = 120, card_height: int = 160):
        os.makedirs(path, exist_ok=True)
        templates_dir = os.path.join(path, 'templates')
        assets_dir = os.path.join(path, 'assets')
        os.makedirs(templates_dir, exist_ok=True)
        os.makedirs(assets_dir, exist_ok=True)
        config = {
            'name': name,
            'card_width': card_width,
            'card_height': card_height,
            'template_perimeters': {},
            'template_order': [],
            'assets': {}
        }
        with open(os.path.join(path, 'config.json'), 'w', encoding='utf-8') as f:
            json.dump(config, f, indent=2)
        return Project(path=path, name=name, card_width=card_width, card_height=card_height)

    @staticmethod
    def open(path: str):
        if not os.path.isdir(path):
            raise FileNotFoundError(path)
        cfg_path = os.path.join(path, 'config.json')
        if not os.path.exists(cfg_path):
            raise FileNotFoundError(f"config.json not found in {path}")
        with open(cfg_path, 'r', encoding='utf-8') as f:
            cfg = json.load(f)
        proj = Project(
            path=path,
            name=cfg.get('name', os.path.basename(path)),
            card_width=cfg.get('card_width', 120),
            card_height=cfg.get('card_height', 160),
            assets=cfg.get('assets', {})
        )
        template_perimeters = cfg.get('template_perimeters', {})
        template_order = cfg.get('template_order')
        templates_dir = os.path.join(path, 'templates')
        if os.path.isdir(templates_dir):
            if template_order and isinstance(template_order, list):
                for name in template_order:
                    csv_path = os.path.join(templates_dir, f"{name}.csv")
                    if os.path.exists(csv_path):
                        try:
                            tpl = Template.load_csv(csv_path)
                            tpl.perimeter = template_perimeters.get(tpl.name, "all")
                            proj.templates[tpl.name] = tpl
                        except Exception:
                            continue
                for fname in sorted(os.listdir(templates_dir)):
                    if fname.lower().endswith('.csv'):
                        name = os.path.splitext(fname)[0]
                        if name not in proj.templates:
                            try:
                                tpl = Template.load_csv(os.path.join(templates_dir, fname))
                                tpl.perimeter = template_perimeters.get(tpl.name, "all")
                                proj.templates[tpl.name] = tpl
                            except Exception:
                                continue
            else:
                for fname in sorted(os.listdir(templates_dir)):
                    if fname.lower().endswith('.csv'):
                        try:
                            tpl = Template.load_csv(os.path.join(templates_dir, fname))
                            tpl.perimeter = template_perimeters.get(tpl.name, "all")
                            proj.templates[tpl.name] = tpl
                        except Exception:
                            continue
        # fallback asset mapping: populate with filenames if config has no assets mapping
        assets_dir = os.path.join(path, proj.assets_dir)
        if os.path.isdir(assets_dir) and not proj.assets:
            for fname in sorted(os.listdir(assets_dir)):
                file_path = os.path.join(assets_dir, fname)
                if os.path.isfile(file_path):
                    proj.assets[fname] = os.path.join(proj.assets_dir, fname)
        return proj

    def save(self):
        template_perimeters = {name: tpl.perimeter for name, tpl in self.templates.items()}
        assets_data = {
            name: os.path.relpath(path, self.path) if path and os.path.isabs(path) else path
            for name, path in self.assets.items()
        }
        config_data = {
            'name': self.name,
            'card_width': self.card_width,
            'card_height': self.card_height,
            'template_perimeters': template_perimeters,
            'template_order': list(self.templates.keys()),
            'assets': assets_data
        }
        with open(os.path.join(self.path, 'config.json'), 'w', encoding='utf-8') as f:
            json.dump(config_data, f, indent=2)
        # save templates
        templates_dir = os.path.join(self.path, 'templates')
        os.makedirs(templates_dir, exist_ok=True)
        for name, tpl in self.templates.items():
            tpl.save_csv(os.path.join(templates_dir, f"{name}.csv"))

    def import_asset(self, src_path: str, asset_name: str):
        assets_dir = os.path.join(self.path, self.assets_dir)
        os.makedirs(assets_dir, exist_ok=True)
        _, ext = os.path.splitext(src_path)
        safe_name = re.sub(r'[^\w\-\. ]+', '_', asset_name).strip() or 'asset'
        dst = os.path.join(assets_dir, safe_name + ext)
        shutil.copy(src_path, dst)
        self.assets[asset_name] = os.path.relpath(dst, self.path)
        return dst

    def asset_path(self, name: str) -> Optional[str]:
        if not name or name not in self.assets:
            return None
        path = self.assets[name]
        if os.path.isabs(path):
            return path
        return os.path.join(self.path, path)

    def list_assets(self) -> List[str]:
        return list(self.assets.keys())

# ---------- Perimeter Logic ----------

def match_perimeter(perimeter: str, row: Dict[str, str]) -> bool:
    if perimeter == "all":
        return True

    parts = perimeter.split(';')
    if len(parts) != 3:
        return False 

    key, comparison ,value = parts[0].strip(), parts[1].strip(), parts[2].strip()
    #print(f"Matching perimeter: key={key}, comparison={comparison}, value={value} against row {row}")
    if key in row:
        #print(f"Perimeter key '{key}' matches row key")
        if comparison == "=":
            return row[key] == value
        if comparison == ">":
            return row[key] > value
        if comparison == ">=":
            return row[key] >= value
        if comparison == "<":
            return row[key] < value
        if comparison == "<=":
            return row[key] <= value
        if comparison == "!=":
            return row[key] != value
        if comparison == "not in":
            print(f"Checking if {row[key]} not in {value}")
            return row[key] not in value
        if comparison == "in":
            return row[key] in value
        if comparison == "between":
            values = value.split(',')
            return values[0] <= row[key] <= values[1]

# ---------- Editor App ----------

class EditorApp:
    def __init__(self, root):
        self.root = root
        self.root.title('Card Template Editor')
        self.project: Optional[Project] = None
        self.current_template: Optional[Template] = None
        self.selected_element_index: Optional[int] = None

        # card size used by canvas and render -- default until project opened
        self.CARD_SIZE = (120, 160)

        # undo/redo stacks store deep copies of templates
        self.undo_stack: List[List[TemplateElement]] = []
        self.redo_stack: List[List[TemplateElement]] = []

        self.setup_ui()
        self.drag_data = {'x':0,'y':0,'item':None,'index':None}
        self.preview_images: Dict[str, ImageTk.PhotoImage] = {}
        self.font_file_map: Dict[str, str] = {}

    def setup_ui(self):
        # Layout: left frame (projects/templates/assets + project settings), center canvas, right props
        self.left_frame = ttk.Frame(self.root, width=240)
        self.left_frame.pack(side=tk.LEFT, fill=tk.Y)
        self.center_frame = ttk.Frame(self.root)
        self.center_frame.pack(side=tk.LEFT, expand=True, fill=tk.BOTH)
        self.right_frame = ttk.Frame(self.root, width=340)
        self.right_frame.pack(side=tk.RIGHT, fill=tk.Y)

        # Left: project controls
        ttk.Label(self.left_frame, text='Project').pack(pady=4)
        ttk.Button(self.left_frame, text='New Project', command=self.new_project).pack(fill=tk.X)
        project_button_frame = ttk.Frame(self.left_frame)
        project_button_frame.pack(fill=tk.X)
        ttk.Button(project_button_frame, text='Open', command=self.open_project, width=10).pack(side=tk.LEFT)
        ttk.Button(project_button_frame, text='Load', command=self.load_project).pack(side=tk.LEFT, fill=tk.X, expand=True, padx=(4,0))
        load_label_frame = ttk.Frame(self.left_frame)
        load_label_frame.pack(fill=tk.X, padx=6, pady=(4,0))
        ttk.Label(load_label_frame, text='Project name:').pack(side=tk.LEFT)
        self.load_project_name_entry = ttk.Entry(load_label_frame)
        self.load_project_name_entry.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=(4,0))
        ttk.Button(self.left_frame, text='Save Project', command=self.save_project).pack(fill=tk.X, pady=(4,0))
        ttk.Separator(self.left_frame).pack(fill=tk.X, pady=6)

        # Project settings (card size)
        ttk.Label(self.left_frame, text='Project Settings').pack(pady=4)
        settings_frame = ttk.Frame(self.left_frame)
        settings_frame.pack(fill=tk.X, padx=6)
        ttk.Label(settings_frame, text='Card width').grid(row=0, column=0, sticky='w')
        self.project_card_w = ttk.Entry(settings_frame, width=8)
        self.project_card_w.grid(row=0, column=1, sticky='w', padx=4)
        ttk.Label(settings_frame, text='Card height').grid(row=1, column=0, sticky='w')
        self.project_card_h = ttk.Entry(settings_frame, width=8)
        self.project_card_h.grid(row=1, column=1, sticky='w', padx=4)
        ttk.Button(settings_frame, text='Apply', command=self.apply_project_settings).grid(row=2, column=0, columnspan=2, pady=4, sticky='ew')
        ttk.Separator(self.left_frame).pack(fill=tk.X, pady=6)

        # Templates list
        ttk.Label(self.left_frame, text='Templates').pack(pady=4)
        self.templates_listbox = tk.Listbox(self.left_frame, height=5)
        self.templates_listbox.pack(fill=tk.X, padx=6)
        self.templates_listbox.bind('<<ListboxSelect>>', self.on_template_select)
        ttk.Button(self.left_frame, text='New Template', command=self.new_template).pack(fill=tk.X, padx=6)
        ttk.Button(self.left_frame, text='Delete Template', command=self.delete_template).pack(fill=tk.X, padx=6)
        # Move buttons side by side
        move_buttons_frame = ttk.Frame(self.left_frame)
        move_buttons_frame.pack(fill=tk.X, padx=6, pady=2)
        ttk.Button(move_buttons_frame, text='Move Up', command=self.move_template_up).pack(side=tk.LEFT, padx=(0,2))
        ttk.Button(move_buttons_frame, text='Move Down', command=self.move_template_down).pack(side=tk.LEFT)
        ttk.Button(self.left_frame, text='Import Template CSV', command=self.import_template_csv).pack(fill=tk.X, padx=6)

        # Perimeter editing
        ttk.Label(self.left_frame, text="Template Perimeter").pack(pady=(6,0))
        self.template_perimeter_entry = ttk.Entry(self.left_frame)
        self.template_perimeter_entry.pack(fill=tk.X, padx=6)
        ttk.Button(self.left_frame, text='Apply Perimeter', command=self.apply_perimeter).pack(fill=tk.X, padx=6, pady=2)

        ttk.Separator(self.left_frame).pack(fill=tk.X, pady=6)

        # Assets
        ttk.Label(self.left_frame, text='Assets').pack(pady=4)
        self.assets_listbox = tk.Listbox(self.left_frame, height=5)
        self.assets_listbox.pack(fill=tk.X, padx=6)
        ttk.Button(self.left_frame, text='Import Asset', command=self.import_asset).pack(fill=tk.X, padx=6)
        ttk.Button(self.left_frame, text='Delete Asset', command=self.delete_asset).pack(fill=tk.X, padx=6)
        ttk.Button(self.left_frame, text='Refresh Assets', command=self.refresh_assets).pack(fill=tk.X, padx=6)

        # Center: canvas and toolbar
        toolbar = ttk.Frame(self.center_frame)
        toolbar.pack(fill=tk.X)
        ttk.Button(toolbar, text='Add Text', command=lambda: self.add_element('text')).pack(side=tk.LEFT)
        ttk.Button(toolbar, text='Add Image', command=lambda: self.add_element('image')).pack(side=tk.LEFT)
        ttk.Button(toolbar, text='Add Rect', command=lambda: self.add_element('rect')).pack(side=tk.LEFT)
        ttk.Button(toolbar, text='Add Circle', command=lambda: self.add_element('circle')).pack(side=tk.LEFT)
        ttk.Button(toolbar, text='Duplicate', command=self.duplicate_element).pack(side=tk.LEFT)
        ttk.Button(toolbar, text='Delete', command=self.delete_selected_element).pack(side=tk.LEFT)
        ttk.Button(toolbar, text='Undo', command=self.undo).pack(side=tk.LEFT)
        ttk.Button(toolbar, text='Redo', command=self.redo).pack(side=tk.LEFT)
        ttk.Button(toolbar, text='Export CSV', command=self.export_current_template).pack(side=tk.LEFT)

        # Project name display above canvas
        self.project_name_frame = ttk.Frame(self.center_frame)
        self.project_name_frame.pack(fill=tk.X, padx=10, pady=(5,0))
        ttk.Label(self.project_name_frame, text="Project:").pack(side=tk.LEFT, padx=(0,6))
        self.project_name_label = ttk.Label(self.project_name_frame, text="(No project loaded)", font=('TkDefaultFont', 10, 'bold'), anchor='w')
        self.project_name_label.pack(side=tk.LEFT, fill=tk.X, expand=True)

        canvas_holder = ttk.Frame(self.center_frame)
        canvas_holder.pack(expand=True, fill=tk.BOTH, padx=10, pady=10)
        self.canvas = tk.Canvas(canvas_holder, width=self.CARD_SIZE[0], height=self.CARD_SIZE[1], bg='white', bd=2, relief=tk.SUNKEN)
        self.canvas.pack(expand=True)
        self.canvas.bind('<ButtonPress-1>', self.on_canvas_press)
        self.canvas.bind('<B1-Motion>', self.on_canvas_drag)
        self.canvas.bind('<ButtonRelease-1>', self.on_canvas_release)
        self.canvas.bind('<Double-Button-1>', self.on_canvas_double)
        self.canvas.bind('<KeyPress-e>', self.on_canvas_key_press)
        self.canvas.bind('<KeyPress-Left>', lambda e: self.move_element(-1, 0))
        self.canvas.bind('<KeyPress-Right>', lambda e: self.move_element(1, 0))
        self.canvas.bind('<KeyPress-Up>', lambda e: self.move_element(0, -1))
        self.canvas.bind('<KeyPress-Down>', lambda e: self.move_element(0, 1))

        # Template perimeter display below canvas
        self.perimeter_display_frame = ttk.Frame(self.center_frame)
        self.perimeter_display_frame.pack(fill=tk.X, padx=10, pady=(0,10))
        ttk.Label(self.perimeter_display_frame, text="Current Perimeter:").pack(side=tk.LEFT, padx=(0,6))
        self.perimeter_display_label = ttk.Label(self.perimeter_display_frame, text="all", relief=tk.SUNKEN, anchor='w')
        self.perimeter_display_label.pack(side=tk.LEFT, fill=tk.X, expand=True)

        # Right: properties
        ttk.Label(self.right_frame, text='Element Properties').pack(pady=4)
        props = self.right_frame
        self.prop_type = ttk.Combobox(props, values=['text','image','rect','circle'])
        self.prop_type.pack(fill=tk.X, padx=6, pady=2)
        ttk.Label(props, text='Value (text or asset name)').pack()
        value_frame = ttk.Frame(props)
        value_frame.pack(fill=tk.X, padx=6, pady=2)
        self.prop_value = ttk.Entry(value_frame)
        self.prop_value.pack(side=tk.LEFT, fill=tk.X, expand=True)
        self.value_edit_button = ttk.Button(value_frame, text='...', command=self.edit_value_text)
        self.value_edit_button.pack(side=tk.LEFT, padx=(4,0))

        ttk.Label(props, text='X').pack()
        self.prop_x = ttk.Entry(props)
        self.prop_x.pack(fill=tk.X, padx=6, pady=2)
        ttk.Label(props, text='Y').pack()
        self.prop_y = ttk.Entry(props)
        self.prop_y.pack(fill=tk.X, padx=6, pady=2)
        ttk.Label(props, text='W').pack()
        self.prop_w = ttk.Entry(props)
        self.prop_w.pack(fill=tk.X, padx=6, pady=2)
        ttk.Label(props, text='H').pack()
        self.prop_h = ttk.Entry(props)
        self.prop_h.pack(fill=tk.X, padx=6, pady=2)
        ttk.Label(props, text='Font').pack()
        self.prop_font = ttk.Entry(props)
        self.prop_font.pack(fill=tk.X, padx=6, pady=2)
        self.prop_font.bind('<KeyRelease>', self.on_font_entry_change)
        ttk.Button(props, text='Refresh fonts', command=self.populate_font_list).pack(fill=tk.X, padx=6, pady=2)
        ttk.Label(props, text='Available fonts').pack()
        self.font_listbox = tk.Listbox(props, height=3)
        self.font_listbox.pack(fill=tk.BOTH, padx=6, pady=2, expand=False)
        self.font_listbox.bind('<<ListboxSelect>>', self.on_font_select)
        self.font_preview_label = ttk.Label(props, text='Sample text', anchor='center')
        self.font_preview_label.pack(fill=tk.X, padx=6, pady=4)
        ttk.Label(props, text='Size').pack()
        self.prop_size = ttk.Entry(props)
        self.prop_size.pack(fill=tk.X, padx=6, pady=2)
        ttk.Button(props, text='Pick Color', command=self.pick_color).pack(padx=6, pady=4)
        ttk.Label(props, text='Anchor').pack()
        self.prop_anchor = ttk.Entry(props)
        self.prop_anchor.pack(fill=tk.X, padx=6, pady=2)
        ttk.Label(props, text='Rotate').pack()
        self.prop_rotate = ttk.Entry(props)
        self.prop_rotate.pack(fill=tk.X, padx=6, pady=2)
        ttk.Label(props, text='Pin').pack()
        self.prop_pin = ttk.Combobox(props, values=['L','C','R'])
        self.prop_pin.pack(fill=tk.X, padx=6, pady=2)
        ttk.Button(props, text='Apply', command=self.apply_properties).pack(fill=tk.X, padx=6, pady=6)

        # Bottom: preview / generator
        gen_frame = ttk.Frame(self.right_frame)
        gen_frame.pack(side=tk.BOTTOM, fill=tk.X, pady=6)
        
        # Sample card values for preview
        ttk.Label(gen_frame, text='Sample Card Values').pack(pady=4)
        self.sample_entry = ttk.Entry(gen_frame)
        self.sample_entry.pack(fill=tk.X, padx=6, pady=2)
        self.sample_entry.insert(0, '1,1,1,1,1')
        
        ttk.Button(gen_frame, text='Preview (as PNG)', command=self.preview_png).pack(fill=tk.X, pady=4)
        ttk.Button(gen_frame, text='Generate Deck (CSV)', command=self.generate_deck).pack(fill=tk.X)

    # ---------- Project actions ----------

    def new_project(self):
        path = filedialog.askdirectory(title='Choose base folder for new project')
        if not path:
            return
        name = simpledialog.askstring('Project name', 'Name of the project')
        if not name:
            return
        # ask sizes
        w = simpledialog.askinteger('Card width', 'Card width (px)', initialvalue=120, minvalue=10)
        h = simpledialog.askinteger('Card height', 'Card height (px)', initialvalue=160, minvalue=10)
        if w is None or h is None:
            return
        proj_path = os.path.join(path, name)
        self.project = Project.create(proj_path, name, card_width=w, card_height=h)
        self.current_template = None
        self.CARD_SIZE = (w, h)
        self.selected_element_index = None
        self.undo_stack.clear(); self.redo_stack.clear()
        self.refresh_ui()
        self.project_name_label.config(text=name)
        messagebox.showinfo('Created', f'Project created at {proj_path}')

    def open_project(self):
        path = filedialog.askdirectory(title='Open project folder')
        if not path:
            return
        try:
            self.project = Project.open(path) 
            self.current_template = None
            self.CARD_SIZE = (self.project.card_width, self.project.card_height)
            self.selected_element_index = None
            self.undo_stack.clear(); self.redo_stack.clear()
            self.refresh_ui()
            self.project_name_label.config(text=self.project.name)
        except Exception as e:
            messagebox.showerror('Error', str(e))

    def load_project(self):
        name = self.load_project_name_entry.get().strip()
        if not name:
            messagebox.showwarning('No project name', 'Enter a project folder name to load')
            return
        path = os.path.join(os.getcwd(), name)
        if not os.path.isdir(path):
            messagebox.showerror('Invalid folder', f'No folder found at: {path}')
            return
        try:
            self.project = Project.open(path)
            self.current_template = None
            self.CARD_SIZE = (self.project.card_width, self.project.card_height)
            self.selected_element_index = None
            self.undo_stack.clear(); self.redo_stack.clear()
            self.refresh_ui()
            self.project_name_label.config(text=self.project.name)
        except Exception as e:
            messagebox.showerror('Error', str(e))

    def save_project(self):
        if not self.project:
            messagebox.showwarning('No project', 'Open or create a project first')
            return
        # before saving, store current template elements
        if self.current_template:
            self.project.templates[self.current_template.name] = self.current_template
        self.project.save()
        messagebox.showinfo('Saved', 'Project saved')

    def apply_project_settings(self):
        if not self.project:
            messagebox.showwarning('No project', 'Open or create a project first')
            return
        try:
            w = int(self.project_card_w.get())
            h = int(self.project_card_h.get())
        except Exception:
            messagebox.showerror('Invalid values', 'Card width/height must be integers')
            return
        self.project.card_width = w
        self.project.card_height = h
        self.CARD_SIZE = (w, h)
        self.canvas.config(width=w, height=h)
        self.project.save()
        self.refresh_canvas()
        messagebox.showinfo('Applied', 'Project settings updated')

    # ---------- Template actions ----------

    def new_template(self):
        if not self.project:
            messagebox.showwarning('No project', 'Create or open a project first')
            return
        name = simpledialog.askstring('Template name', 'Template name')
        if not name:
            return
        if name in self.project.templates:
            messagebox.showwarning('Exists', f'Template with name {name} already exists')
            return
        tpl = Template(name=name)
        self.project.templates[name] = tpl
        self.current_template = tpl
        self.selected_element_index = None
        self.push_undo()
        self.refresh_ui()

    def delete_template(self):
        if not self.project:
            return
        sel = self.templates_listbox.curselection()
        if not sel:
            return
        name = self.templates_listbox.get(sel[0])
        if messagebox.askyesno('Delete', f'Delete template {name}?'):
            del self.project.templates[name]
            self.current_template = None
            self.refresh_ui()

    def import_template_csv(self):
        path = filedialog.askopenfilename(title='Select CSV template', filetypes=[('CSV','*.csv')])
        if not path:
            return
        tpl = Template.load_csv(path)
        if not self.project:
            messagebox.showwarning('No project', 'Open a project first to import templates into it')
            return
        self.project.templates[tpl.name] = tpl
        self.current_template = tpl
        self.push_undo()
        self.refresh_ui()

    def _reorder_templates(self, new_order: List[str]):
        if not self.project:
            return
        old_templates = self.project.templates
        self.project.templates = {name: old_templates[name] for name in new_order if name in old_templates}

    def move_template_up(self):
        if not self.project:
            return
        sel = self.templates_listbox.curselection()
        if not sel:
            return
        idx = sel[0]
        if idx <= 0:
            return
        names = list(self.project.templates.keys())
        names[idx-1], names[idx] = names[idx], names[idx-1]
        self._reorder_templates(names)
        self.refresh_ui()
        self.templates_listbox.select_set(idx-1)
        self.templates_listbox.event_generate('<<ListboxSelect>>')

    def move_template_down(self):
        if not self.project:
            return
        sel = self.templates_listbox.curselection()
        if not sel:
            return
        idx = sel[0]
        names = list(self.project.templates.keys())
        if idx >= len(names)-1:
            return
        names[idx], names[idx+1] = names[idx+1], names[idx]
        self._reorder_templates(names)
        self.refresh_ui()
        self.templates_listbox.select_set(idx+1)
        self.templates_listbox.event_generate('<<ListboxSelect>>')

    def export_current_template(self):
        if not self.current_template:
            return
        path = filedialog.asksaveasfilename(defaultextension='.csv', filetypes=[('CSV','*.csv')], initialfile=f'{self.current_template.name}.csv')
        if not path:
            return
        self.current_template.save_csv(path)
        messagebox.showinfo('Exported', f'Exported to {path}')

    # ---------- Assets ----------

    def import_asset(self):
        if not self.project:
            messagebox.showwarning('No project', 'Open/create project first')
            return
        paths = filedialog.askopenfilenames(title='Select asset(s)')
        for p in paths:
            name_default = os.path.splitext(os.path.basename(p))[0]
            asset_name = simpledialog.askstring('Asset name', 'Enter a name for this asset', initialvalue=name_default)
            if not asset_name:
                continue
            if asset_name in self.project.assets:
                if not messagebox.askyesno('Overwrite asset', f'Asset "{asset_name}" already exists. Overwrite?'):
                    continue
            try:
                self.project.import_asset(p, asset_name)
            except Exception as e:
                print("Asset import failed:", e)
        self.project.save()
        self.refresh_assets()

    def refresh_assets(self):
        self.assets_listbox.delete(0, tk.END)
        if not self.project:
            return
        for a in self.project.list_assets():
            self.assets_listbox.insert(tk.END, os.path.basename(a))

    def delete_asset(self):
        if not self.project:
            messagebox.showwarning('No project', 'Open/create a project first')
            return
        sel = self.assets_listbox.curselection()
        if not sel:
            return
        asset_name = self.assets_listbox.get(sel[0])
        asset_path = self.project.asset_path(asset_name)
        if not asset_path or not os.path.exists(asset_path):
            messagebox.showwarning('Missing asset', f'Asset not found: {asset_name}')
            self.refresh_assets()
            return
        if not messagebox.askyesno('Delete Asset', f'Delete asset {asset_name}?'):
            return
        try:
            os.remove(asset_path)
            del self.project.assets[asset_name]
            self.project.assets.pop(asset_name, None)
            self.project.save()
            self.refresh_assets()
            messagebox.showinfo('Deleted', f'Asset deleted: {asset_name}')
        except Exception as e:
            messagebox.showerror('Error', f'Failed to delete asset: {e}')

    # ---------- Canvas / Elements ----------

    def add_element(self, etype: str):
        if not self.project or not self.current_template:
            messagebox.showwarning('No template', 'Open or create a template in a project')
            return
        e = TemplateElement(type=etype, value='{rank}' if etype=='text' else '', x=20, y=20, size=24, color='#000000')
        if etype == 'image':
            # choose image
            sel = self.assets_listbox.curselection()
            if sel and self.project:
                fname = self.assets_listbox.get(sel[0])
                e.value = os.path.join(self.project.path, self.project.assets_dir, fname)
        self.current_template.elements.append(e)
        self.selected_element_index = len(self.current_template.elements)-1
        self.push_undo()
        self.refresh_canvas()
        self.fill_properties_from_selected()
        # update perimeter entry and display
        if self.current_template:
            self.template_perimeter_entry.delete(0, tk.END)
            self.template_perimeter_entry.insert(0, self.current_template.perimeter)
            self.perimeter_display_label.config(text=self.current_template.perimeter)

    def apply_perimeter(self):
        if not self.current_template:
            return
        new_perimeter = self.template_perimeter_entry.get()
        self.current_template.perimeter = new_perimeter
        self.perimeter_display_label.config(text=new_perimeter)
        self.project.save() # save project to persist perimeter change
        messagebox.showinfo('Perimeter Applied', f'Perimeter set to: {new_perimeter}')

    def duplicate_element(self):
        if not self.current_template or self.selected_element_index is None:
            return
        src = self.current_template.elements[self.selected_element_index]
        copy_e = TemplateElement(**asdict(src))
        copy_e.x += 10; copy_e.y += 10
        self.current_template.elements.append(copy_e)
        self.selected_element_index = len(self.current_template.elements)-1
        self.push_undo()
        self.refresh_canvas()

    def delete_selected_element(self):
        if not self.current_template or self.selected_element_index is None:
            return
        del self.current_template.elements[self.selected_element_index]
        self.selected_element_index = None
        self.push_undo()
        self.refresh_canvas()

    def on_template_select(self, _ev=None):
        sel = self.templates_listbox.curselection()
        if not sel or not self.project:
            return
        name = self.templates_listbox.get(sel[0])
        self.current_template = self.project.templates.get(name)
        self.selected_element_index = None
        self.push_undo()
        self.refresh_canvas()
        self.fill_properties_from_selected()
        # update perimeter entry and display
        if self.current_template:
            self.template_perimeter_entry.delete(0, tk.END)
            self.template_perimeter_entry.insert(0, self.current_template.perimeter)
            self.perimeter_display_label.config(text=self.current_template.perimeter)

    # ---------- Canvas interaction (drag/drop) ----------

    def on_canvas_press(self, event):
        if not self.current_template:
            return
        self.canvas.focus_set()
        x = event.x; y = event.y
        idx = self.find_element_at(x, y)
        if idx is not None:
            self.selected_element_index = idx
            self.drag_data['item'] = idx
            self.drag_data['x'] = x; self.drag_data['y'] = y
            self.drag_data['index'] = idx
            self.fill_properties_from_selected()
        else:
            # deselect
            self.selected_element_index = None
            self.fill_properties_from_selected()
        # update x and y fields with click coordinates
        self.prop_x.delete(0, tk.END)
        self.prop_x.insert(0, str(x))
        self.prop_y.delete(0, tk.END)
        self.prop_y.insert(0, str(y))
        self.refresh_canvas()

    def on_canvas_drag(self, event):
        if not self.current_template or self.drag_data['item'] is None:
            return
        dx = event.x - self.drag_data['x']
        dy = event.y - self.drag_data['y']
        idx = self.drag_data['item']
        el = self.current_template.elements[idx]
        el.x += dx; el.y += dy
        self.drag_data['x'] = event.x; self.drag_data['y'] = event.y
        # update x and y fields during drag
        self.prop_x.delete(0, tk.END)
        self.prop_x.insert(0, str(el.x))
        self.prop_y.delete(0, tk.END)
        self.prop_y.insert(0, str(el.y))
        self.refresh_canvas()

    def on_canvas_release(self, event):
        if self.drag_data['item'] is not None:
            self.push_undo()
        self.drag_data = {'x':0,'y':0,'item':None,'index':None}

    def on_canvas_key_press(self, event):
        if event.keysym == 'e':
            self.select_next_element()

    def select_next_element(self):
        if not self.current_template or not self.current_template.elements:
            return
        if self.selected_element_index is None:
            self.selected_element_index = 0
        else:
            self.selected_element_index = (self.selected_element_index + 1) % len(self.current_template.elements)
        self.fill_properties_from_selected()
        self.refresh_canvas()

    def move_element(self, dx, dy):
        if not self.current_template or self.selected_element_index is None:
            return
        el = self.current_template.elements[self.selected_element_index]
        el.x += dx
        el.y += dy
        self.push_undo()
        self.fill_properties_from_selected()
        self.refresh_canvas()

    def on_canvas_double(self, event):
        # open quick edit for text
        idx = self.find_element_at(event.x, event.y)
        if idx is None:
            return
        el = self.current_template.elements[idx]
        if el.type == 'text':
            new = simpledialog.askstring('Edit text', 'Value', initialvalue=el.value)
            if new is not None:
                el.value = new
                self.push_undo()
                self.refresh_canvas()
                self.fill_properties_from_selected()

    def find_element_at(self, x, y) -> Optional[int]:
        # find topmost element (iterate reversed)
        if not self.current_template:
            return None
        for i in range(len(self.current_template.elements)-1, -1, -1):
            el = self.current_template.elements[i]
            if el.type == 'text':
                placeholders = {
                    'name': "name",
                    'rank': "RK",
                    'suit': "suit",
                    'value': "V",
                    'tag': "tag"
                }
                text_value = str(el.value)
                for k, v in placeholders.items():
                    text_value = text_value.replace(f"{{{k}}}", v)
                ex = self._get_text_display_x(el, text_value)
                ew = self._measure_text_width(text_value, el.font, el.size)
                eh = el.size + 6
                top = el.y
            else:
                ex, top = el.x, el.y
                ew = el.w or 60
                eh = el.h or 30
            left = ex; right = ex + ew; bottom = top + eh
            if left <= x <= right and top <= y <= bottom:
                return i
        return None

    # ---------- Properties panel ----------

    def fill_properties_from_selected(self):
        if not self.current_template or self.selected_element_index is None:
            # clear fields
            try:
                self.prop_type.set('')
                self.prop_pin.set('')
            except Exception:
                pass
            self.prop_value.delete(0, tk.END)
            for w in (self.prop_x, self.prop_y, self.prop_w, self.prop_h, self.prop_font, self.prop_size, self.prop_anchor, self.prop_rotate):
                w.delete(0, tk.END)
            return
        el = self.current_template.elements[self.selected_element_index]
        self.prop_type.set(el.type)
        self.prop_value.delete(0, tk.END); self.prop_value.insert(0, el.value)
        self.prop_x.delete(0, tk.END); self.prop_x.insert(0, str(el.x))
        self.prop_y.delete(0, tk.END); self.prop_y.insert(0, str(el.y))
        self.prop_w.delete(0, tk.END); self.prop_w.insert(0, str(el.w or ''))
        self.prop_h.delete(0, tk.END); self.prop_h.insert(0, str(el.h or ''))
        self.prop_font.delete(0, tk.END); self.prop_font.insert(0, el.font)
        self._select_font_in_listbox(el.font)
        self.update_font_preview(el.font)
        self.prop_size.delete(0, tk.END); self.prop_size.insert(0, str(el.size))
        self.prop_anchor.delete(0, tk.END); self.prop_anchor.insert(0, el.anchor)
        self.prop_rotate.delete(0, tk.END); self.prop_rotate.insert(0, str(el.rotate))
        self.prop_pin.set(el.pin)

    def apply_properties(self):
        if not self.current_template or self.selected_element_index is None:
            return
        el = self.current_template.elements[self.selected_element_index]
        el.type = self.prop_type.get() or el.type
        el.value = self.prop_value.get() or el.value
        try:
            el.x = int(self.prop_x.get())
            el.y = int(self.prop_y.get())
        except ValueError:
            pass
        try:
            el.w = int(self.prop_w.get()) if self.prop_w.get() else None
            el.h = int(self.prop_h.get()) if self.prop_h.get() else None
        except ValueError:
            pass
        el.font = self.prop_font.get() or el.font
        try:
            el.size = int(self.prop_size.get())
        except ValueError:
            pass
        el.anchor = self.prop_anchor.get() or el.anchor
        try:
            el.rotate = float(self.prop_rotate.get())
        except ValueError:
            pass
        el.pin = self.prop_pin.get() or el.pin
        self.push_undo()
        self.refresh_canvas()

    def pick_color(self):
        c = colorchooser.askcolor()[1]
        if c and self.current_template and self.selected_element_index is not None:
            self.current_template.elements[self.selected_element_index].color = c
            self.push_undo()
            self.refresh_canvas()

    def edit_value_text(self):
        if not self.current_template or self.selected_element_index is None:
            return
        current_value = self.prop_value.get()
        dialog = tk.Toplevel(self.root)
        dialog.title('Edit Value')
        dialog.geometry('400x600')
        text_area = tk.Text(dialog, wrap=tk.WORD)
        text_area.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        text_area.insert(tk.END, current_value)
        button_frame = ttk.Frame(dialog)
        button_frame.pack(side=tk.BOTTOM, fill=tk.X, padx=10, pady=(0,10))
        def on_ok():
            new_value = text_area.get(1.0, tk.END).strip()
            self.prop_value.delete(0, tk.END)
            self.prop_value.insert(0, new_value)
            self.apply_properties()
            dialog.destroy()
        def on_cancel():
            dialog.destroy()
        ttk.Button(button_frame, text='OK', command=on_ok).pack(side=tk.LEFT)
        ttk.Button(button_frame, text='Cancel', command=on_cancel).pack(side=tk.LEFT, padx=(10,0))

    def _find_system_fonts(self) -> Dict[str, str]:
        fonts: Dict[str, str] = {}
        search_dirs = [
            os.path.expanduser('~/.fonts'),
            os.path.expanduser('~/.local/share/fonts'),
            '/usr/share/fonts',
            '/usr/local/share/fonts'
        ]
        for root_dir in search_dirs:
            if not root_dir or not os.path.isdir(root_dir):
                continue
            for root, _, files in os.walk(root_dir):
                for fname in files:
                    if fname.lower().endswith(('.ttf', '.otf', '.ttc')):
                        path = os.path.join(root, fname)
                        fonts[fname.lower()] = path
        return fonts

    def populate_font_list(self):
        self.font_file_map = self._find_system_fonts()
        self.font_listbox.delete(0, tk.END)
        for fname in sorted(self.font_file_map.keys()):
            self.font_listbox.insert(tk.END, fname)

    def on_font_select(self, _event=None):
        sel = self.font_listbox.curselection()
        if not sel:
            return
        font_name = self.font_listbox.get(sel[0])
        self.prop_font.delete(0, tk.END)
        self.prop_font.insert(0, font_name)
        self.update_font_preview(font_name)

    def on_font_entry_change(self, _event=None):
        font_name = self.prop_font.get().strip()
        if font_name:
            self.update_font_preview(font_name)

    def _select_font_in_listbox(self, font_name: str):
        self.font_listbox.selection_clear(0, tk.END)
        if not font_name:
            return
        font_name = font_name.lower()
        for idx in range(self.font_listbox.size()):
            if self.font_listbox.get(idx).lower() == font_name:
                self.font_listbox.selection_set(idx)
                self.font_listbox.see(idx)
                return

    def _get_font_path(self, font_name: str) -> Optional[str]:
        if not font_name:
            return None
        if os.path.isabs(font_name) and os.path.exists(font_name):
            return font_name
        key = font_name.lower()
        if key in self.font_file_map:
            return self.font_file_map[key]
        # allow partial matches against the base file name
        for fname, path in self.font_file_map.items():
            if fname.startswith(key):
                return path
        return None

    def _load_font(self, font_name: str, size: int):
        path = self._get_font_path(font_name)
        if path:
            try:
                return ImageFont.truetype(path, size)
            except Exception:
                pass
        if font_name:
            try:
                return ImageFont.truetype(font_name, size)
            except Exception:
                pass
        for fallback in ['DejaVuSans.ttf', 'LiberationSans-Regular.ttf', 'FreeSans.ttf']:
            try:
                return ImageFont.truetype(fallback, size)
            except Exception:
                continue
        return ImageFont.load_default()

    def _parse_asset_enum_value(self, value):
        if isinstance(value, dict):
            return value
        if not isinstance(value, str):
            return None
        value = value.strip()
        if not value.startswith('{'):
            return None
        try:
            return json.loads(value)
        except json.JSONDecodeError:
            # Support unquoted keys like {asset_enum : {...}} and single quotes
            normalized = value.replace("'", '"')
            normalized = re.sub(r'([{,]\s*)([A-Za-z_][A-Za-z0-9_]*)\s*:', r'\1"\2":', normalized)
            try:
                return json.loads(normalized)
            except json.JSONDecodeError:
                return None

    def _resolve_asset_path(self, value: str) -> Optional[str]:
        if not value:
            return None
        if self.project:
            # direct asset name lookup
            asset_path = self.project.asset_path(value)
            if asset_path and os.path.exists(asset_path):
                return asset_path
        # placeholder syntax support
        if value.startswith('{asset:') and value.endswith('}') and self.project:
            asset_name = value[7:-1]
            asset_path = self.project.asset_path(asset_name)
            if asset_path and os.path.exists(asset_path):
                return asset_path
        # fallback to direct file path
        if os.path.exists(value):
            return value
        return None

    def update_font_preview(self, font_name: str):
        try:
            display_font = tkfont.Font(family=font_name.split('.')[0], size=12)
            self.font_preview_label.configure(font=display_font, text=f'1234567890')
        except Exception:
            self.font_preview_label.configure(font=None, text=f'{font_name} (unavailable)')

    # ---------- Undo / Redo ----------

    def push_undo(self):
        if not self.current_template:
            return
        # store deep copy of elements (convert to dicts)
        snapshot = [TemplateElement(**asdict(e)) for e in self.current_template.elements]
        self.undo_stack.append(snapshot)
        self.redo_stack.clear()

    def undo(self):
        if not self.current_template or not self.undo_stack:
            return
        current = [TemplateElement(**asdict(e)) for e in self.current_template.elements]
        self.redo_stack.append(current)
        snap = self.undo_stack.pop()
        self.current_template.elements = [TemplateElement(**asdict(e)) for e in snap]
        self.selected_element_index = None
        self.refresh_canvas()

    def redo(self):
        if not self.current_template or not self.redo_stack:
            return
        self.undo_stack.append([TemplateElement(**asdict(e)) for e in self.current_template.elements])
        snap = self.redo_stack.pop()
        self.current_template.elements = [TemplateElement(**asdict(e)) for e in snap]
        self.refresh_canvas()

    # ---------- Rendering ----------

    def refresh_ui(self):
        # update templates listbox
        self.templates_listbox.delete(0, tk.END)
        if self.project:
            for name in self.project.templates:
                self.templates_listbox.insert(tk.END, name)
            # fill project settings entries
            self.project_card_w.delete(0, tk.END); self.project_card_w.insert(0, str(self.project.card_width))
            self.project_card_h.delete(0, tk.END); self.project_card_h.insert(0, str(self.project.card_height))
            # update project name display
            self.project_name_label.config(text=self.project.name)
            # apply card size
            self.CARD_SIZE = (self.project.card_width, self.project.card_height)
            self.canvas.config(width=self.CARD_SIZE[0], height=self.CARD_SIZE[1])
        else:
            self.project_card_w.delete(0, tk.END); self.project_card_h.delete(0, tk.END)
            self.project_name_label.config(text="(No project loaded)")
        self.refresh_assets()
        self.populate_font_list()
        self.refresh_canvas()

    def refresh_canvas(self):
        self.canvas.delete('all')
        # draw card background
        self.canvas.create_rectangle(0, 0, self.CARD_SIZE[0], self.CARD_SIZE[1], fill='white', outline='black')
        if not self.current_template:
            return
        # draw elements in order
        for idx, el in enumerate(self.current_template.elements):
            _ = self.draw_element_on_canvas(el, idx==self.selected_element_index)
        # show selection rectangle if any
        if self.selected_element_index is not None and self.selected_element_index < len(self.current_template.elements):
            el = self.current_template.elements[self.selected_element_index]
            if el.type == 'text':
                text_value = str(el.value)
                x0 = self._get_text_display_x(el, text_value)
                ew = self._measure_text_width(text_value, el.font, el.size)
                eh = el.size + 6
                y0 = el.y
            else:
                x0 = el.x
                y0 = el.y
                ew = el.w or 40
                eh = el.h or 30
            self.canvas.create_rectangle(x0-2, y0-2, x0+ew+2, y0+eh+2, outline='blue', dash=(4,2))

    def _measure_text_width(self, text: str, font_name: str, size: int) -> int:
        try:
            f = tkfont.Font(family=font_name.split('.')[0], size=size)
            return f.measure(text)
        except Exception:
            return max(10, len(text) * size // 2)

    def _get_text_display_x(self, el: TemplateElement, text: str) -> int:
        width = self._measure_text_width(text, el.font, el.size)
        if el.pin == 'C':
            return el.x - width // 2
        if el.pin == 'R':
            return el.x - width
        return el.x

    def draw_element_on_canvas(self, el: TemplateElement, selected: bool=False):
        # For text: use TK text
        if el.type == 'text':
            # placeholder rendering: show value literally (placeholders not expanded here)
            placeholders = {
                'name': "name",
                'rank': "RK",
                'suit': "suit",
                'value': "V",
                'tag': "tag"
            }
            text_value = el.value
            for k, v in placeholders.items():
                text_value = text_value.replace(f"{{{k}}}", v)
            x = self._get_text_display_x(el, text_value)
            try:
                self.canvas.create_text(x, el.y, text=text_value, anchor='nw', font=(el.font.split(".")[0], el.size), fill=el.color)
            except Exception:
                self.canvas.create_text(x, el.y, text=text_value, anchor='nw', fill=el.color)
        elif el.type == 'image':
            imgpath = self._resolve_asset_path(el.value)
            if imgpath:
                key = imgpath + f"_{el.w}_{el.h}"
                try:
                    pil = Image.open(imgpath)
                except Exception:
                    pil = None
                if pil is not None:
                    if el.w and el.h:
                        pil = ImageOps.contain(pil, (el.w, el.h))
                    else:
                        pil = ImageOps.contain(pil, (100,100))
                    tkimg = ImageTk.PhotoImage(pil)
                    # keep reference
                    self.preview_images[key] = tkimg
                    self.canvas.create_image(el.x, el.y, image=tkimg, anchor='nw')
                else:
                    self.canvas.create_rectangle(el.x, el.y, el.x+(el.w or 60), el.y+(el.h or 40), fill='gray')
                    self.canvas.create_text(el.x+4, el.y+4, text=el.value or 'image', anchor='nw')
            else:
                # simple rect placeholder
                self.canvas.create_rectangle(el.x, el.y, el.x+(el.w or 60), el.y+(el.h or 40), fill='gray')
                self.canvas.create_text(el.x+4, el.y+4, text=el.value or 'image', anchor='nw')
        elif el.type == 'rect':
            self.canvas.create_rectangle(el.x, el.y, el.x+(el.w or 60), el.y+(el.h or 30), fill=el.color)
        elif el.type == 'circle':
            r = el.w or 20
            self.canvas.create_oval(el.x-r, el.y-r, el.x+r, el.y+r, fill=el.color)
        else:
            self.canvas.create_text(el.x, el.y, text='?', anchor='nw')

    # ---------- Preview / Generate ----------

    def _render_template_to_image(self, template: Template, placeholders: Dict[str,str], pil : Image.Image) -> Image.Image:
        #pil = Image.new('RGBA', (w, h), 'white')
        draw = ImageDraw.Draw(pil)
        for el in template.elements:
            if el.type == 'text':
                # replace placeholders in text
                text_val = str(el.value)
                for k, v in placeholders.items():
                    text_val = text_val.replace(f"{{{k}}}", v)
                font = self._load_font(el.font, el.size)
                left, _, right, _ = font.getbbox(text_val)
                width = right - left
                if el.pin == 'C':
                    x = el.x - width // 2
                elif el.pin == 'R':
                    x = el.x - width
                else:
                    x = el.x
                draw.text((x, el.y), text_val, fill=el.color, font=font)
            elif el.type == 'image':
                imgpath = None
                asset_data = self._parse_asset_enum_value(el.value)
                if isinstance(asset_data, dict) and 'asset_enum' in asset_data:
                    #print("Parsed asset enum:", asset_data)
                    asset_enums = asset_data.get('asset_enum', {})
                    asset_type = asset_enums.get('type', '')
                    asset_key = placeholders.get(asset_type, '')
                    #print(f"Looking up asset for type '{asset_type}' with key '{asset_key}'")
                    val = asset_enums.get(asset_key, '')
                    imgpath = self._resolve_asset_path(val)
                    #print(f"Resolved asset path from enum: {imgpath}")
                if not imgpath:
                    imgpath = self._resolve_asset_path(el.value)
                if imgpath and os.path.exists(imgpath):
                    try:
                        im = Image.open(imgpath).convert('RGBA')
                        if el.w and el.h:
                            im = ImageOps.contain(im, (el.w, el.h))
                        pil.paste(im, (el.x, el.y), im)
                    except Exception:
                        # skip if image fails
                        pass
            elif el.type == 'rect':
                draw.rectangle((el.x, el.y, el.x+(el.w or 60), el.y+(el.h or 30)), fill=el.color)
            elif el.type == 'circle':
                r = el.w or 20
                draw.ellipse((el.x-r, el.y-r, el.x+r, el.y+r), fill=el.color)
        return pil

    def preview_png(self):
        if not self.project:
            messagebox.showwarning('No project', 'Open a project first')
            return
        
        # Dialog to select templates
        dialog = tk.Toplevel(self.root)
        dialog.title('Select Templates for Preview')
        dialog.geometry('300x400')
        dialog.grab_set()  # Make modal
        
        ttk.Label(dialog, text='Select templates to use for preview:').pack(pady=10)
        
        listbox = tk.Listbox(dialog, selectmode=tk.MULTIPLE, height=10)
        listbox.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        # Populate listbox with template names
        template_names = list(self.project.templates.keys())
        for name in template_names:
            listbox.insert(tk.END, name)
        
        # Pre-select current template if exists
        if self.current_template and self.current_template.name in template_names:
            idx = template_names.index(self.current_template.name)
            listbox.selection_set(idx)
        
        selected_templates = []
        
        def on_ok():
            nonlocal selected_templates
            selected_indices = listbox.curselection()
            selected_templates = [template_names[i] for i in selected_indices]
            dialog.destroy()
        
        def on_cancel():
            dialog.destroy()
        
        button_frame = ttk.Frame(dialog)
        button_frame.pack(fill=tk.X, padx=10, pady=(0,10))
        ttk.Button(button_frame, text='OK', command=on_ok).pack(side=tk.LEFT, padx=(0,5))
        ttk.Button(button_frame, text='Cancel', command=on_cancel).pack(side=tk.LEFT)
        
        self.root.wait_window(dialog)
        
        if not selected_templates:
            messagebox.showwarning('No selection', 'Please select at least one template for preview')
            return
        
        # use sample values from input fields
        row = self.sample_entry.get().split(',') if self.sample_entry.get() else []
        placeholders = {
                'name': row[0] if len(row) > 0 else 'Sample Card',
                'rank': row[1] if len(row) > 1 else '',
                'suit': row[2] if len(row) > 2 else '',
                'value': row[3] if len(row) > 3 else '',
                'tag': row[4] if len(row) > 4 else ''
            }
        w, h = self.CARD_SIZE
        pil = Image.new('RGBA', (w, h), 'white')
        for name in selected_templates:
            tpl = self.project.templates[name]
            pil = self._render_template_to_image(tpl, placeholders, pil)
        outpath = os.path.join(self.project.path, 'preview.png')
        pil.save(outpath)
        
        # Display the preview in a new window
        preview_window = tk.Toplevel(self.root)
        preview_window.title('Preview')
        
        # Convert PIL image to PhotoImage
        pil_display = pil.convert('RGB') if pil.mode == 'RGBA' else pil
        photo = ImageTk.PhotoImage(pil_display)
        
        # Display image in label
        label = tk.Label(preview_window, image=photo)
        label.image = photo  # Keep a reference to prevent garbage collection
        label.pack(padx=10, pady=10)
        
        # Add a close button
        ttk.Button(preview_window, text='Close', command=preview_window.destroy).pack(pady=5)

    def _safe_filename(self, name: str) -> str:
        # simple slugify: keep alnum, dash, underscore
        name = name or ''
        name = re.sub(r'[^\w\-]+', '_', name)
        return name

    def generate_deck(self):
        rows = self.open_csv()

        # render each row
        out_folder = os.path.join(self.project.path, 'playing_cards')
        os.makedirs(out_folder, exist_ok=True)
        csv_path = os.path.join(self.project.path, self.project.name+'_cards_dict.csv')
        with open(csv_path, 'w', newline='', encoding='utf-8') as csvfile:
            writer = csv.writer(csvfile)
            for i, r in enumerate(rows, start=1):
                placeholders = {
                    'name': r.get('nom_carte') or r.get('name') or '',
                    'rank': r.get('rank', ''),
                    'suit': r.get('suit', ''),
                    'value': r.get('value', ''),
                    'tag': r.get('tag', '')
                }
                w, h = self.CARD_SIZE
                pil = Image.new('RGBA', (w, h), 'white')
                for name, tpl in self.project.templates.items():
                    if match_perimeter(tpl.perimeter, r):
                        pil = self._render_template_to_image(tpl, placeholders, pil)
                outname = f"{i}.png"
                outpath = os.path.join(out_folder, outname)
                try:
                    pil.save(outpath)
                except Exception:
                    try:
                        pil.convert('RGB').save(outpath)
                    except Exception as e:
                        print('Failed to save', outpath, e)
                        outpath = ''
                relative_path = os.path.join('playing_cards', outname)
                writer.writerow([placeholders.get('name'), relative_path])
        messagebox.showinfo('Generated', f'Generated {len(rows)} cards into {out_folder} and wrote {csv_path}')

    def open_csv(self):
        if not self.current_template or not self.project:
            messagebox.showwarning('No template', 'Open a project and select a template')
            return
        #csv_path = filedialog.askopenfilename(title='Select deck definition CSV', filetypes=[('CSV','*.csv'), ('All','*.*')])
        csv_path = os.path.join(self.project.path, self.project.name+'_cards.csv')
        if not csv_path:
            return
        # read CSV with delimiter ; and expected columns nom_carte;rank;suit;value;tag
        rows = []
        try:
            with open(csv_path, newline='', encoding='utf-8') as f:
                reader = csv.DictReader(f, delimiter=';')
                # if DictReader fieldnames are None or too few, fall back to simple split
                if not reader.fieldnames or len(reader.fieldnames) < 2:
                    f.seek(0)
                    for line in f:
                        line = line.strip()
                        if not line:
                            continue
                        parts = line.split(',')
                        while len(parts) < 5:
                            parts.append('')
                        rows.append({'nom_carte': parts[0], 'rank': parts[1], 'suit': parts[2], 'value': parts[3], 'tag': parts[4]})
                else:
                    for r in reader:
                        rows.append(r)
        except Exception as e:
            messagebox.showerror('Read error', f'Failed to read CSV: {e}')
            return
        if not rows:
            messagebox.showwarning('Empty', 'No rows found in CSV')
            return

        return rows
# ---------- Run ----------

if __name__ == '__main__':
    # quick sanity checks
    try:
        root = tk.Tk()
    except Exception as e:
        print("Tkinter initialization failed:", e)
        raise
    app = EditorApp(root)
    try:
        root.mainloop()
    except KeyboardInterrupt:
        print("Application interrupted by user.")
        root.quit()
