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
import tkinter as tk
from tkinter import filedialog, messagebox, simpledialog, colorchooser
from tkinter import ttk
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

    def to_csv_row(self):
        return [self.type, self.value, str(self.x), str(self.y), str(self.w or ''), str(self.h or ''), self.font, str(self.size), self.color, self.anchor, str(self.rotate)]

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
            rotate=float(row[10]) if len(row)>10 and row[10] else 0.0
        )

@dataclass
class Template:
    name: str
    elements: List[TemplateElement] = field(default_factory=list)

    def save_csv(self, path: str):
        with open(path, 'w', newline='', encoding='utf-8') as f:
            writer = csv.writer(f)
            writer.writerow(['type','value','x','y','w','h','font','size','color','anchor','rotate'])
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
        config = {'name': name, 'card_width': card_width, 'card_height': card_height}
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
        proj = Project(path=path, name=cfg.get('name', os.path.basename(path)), card_width=cfg.get('card_width', 120), card_height=cfg.get('card_height', 160))
        # load templates
        templates_dir = os.path.join(path, 'templates')
        if os.path.isdir(templates_dir):
            for fname in os.listdir(templates_dir):
                if fname.lower().endswith('.csv'):
                    try:
                        tpl = Template.load_csv(os.path.join(templates_dir, fname))
                        proj.templates[tpl.name] = tpl
                    except Exception:
                        # skip malformed templates
                        continue
        return proj

    def save(self):
        with open(os.path.join(self.path, 'config.json'), 'w', encoding='utf-8') as f:
            json.dump({'name': self.name, 'card_width': self.card_width, 'card_height': self.card_height}, f, indent=2)
        # save templates
        templates_dir = os.path.join(self.path, 'templates')
        os.makedirs(templates_dir, exist_ok=True)
        for name, tpl in self.templates.items():
            tpl.save_csv(os.path.join(templates_dir, f"{name}.csv"))

    def import_asset(self, src_path: str):
        assets_dir = os.path.join(self.path, self.assets_dir)
        os.makedirs(assets_dir, exist_ok=True)
        dst = os.path.join(assets_dir, os.path.basename(src_path))
        shutil.copy(src_path, dst)
        return dst

    def list_assets(self) -> List[str]:
        assets_dir = os.path.join(self.path, self.assets_dir)
        if not os.path.isdir(assets_dir):
            return []
        return [os.path.join(assets_dir, f) for f in os.listdir(assets_dir)]

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
        ttk.Button(self.left_frame, text='Open Project', command=self.open_project).pack(fill=tk.X)
        ttk.Button(self.left_frame, text='Save Project', command=self.save_project).pack(fill=tk.X)
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
        self.templates_listbox = tk.Listbox(self.left_frame, height=8)
        self.templates_listbox.pack(fill=tk.X, padx=6)
        self.templates_listbox.bind('<<ListboxSelect>>', self.on_template_select)
        ttk.Button(self.left_frame, text='New Template', command=self.new_template).pack(fill=tk.X, padx=6)
        ttk.Button(self.left_frame, text='Delete Template', command=self.delete_template).pack(fill=tk.X, padx=6)
        ttk.Button(self.left_frame, text='Import Template CSV', command=self.import_template_csv).pack(fill=tk.X, padx=6)
        ttk.Separator(self.left_frame).pack(fill=tk.X, pady=6)

        # Assets
        ttk.Label(self.left_frame, text='Assets').pack(pady=4)
        self.assets_listbox = tk.Listbox(self.left_frame, height=8)
        self.assets_listbox.pack(fill=tk.X, padx=6)
        ttk.Button(self.left_frame, text='Import Asset', command=self.import_asset).pack(fill=tk.X, padx=6)
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

        canvas_holder = ttk.Frame(self.center_frame)
        canvas_holder.pack(expand=True, fill=tk.BOTH, padx=10, pady=10)
        self.canvas = tk.Canvas(canvas_holder, width=self.CARD_SIZE[0], height=self.CARD_SIZE[1], bg='white', bd=2, relief=tk.SUNKEN)
        self.canvas.pack(expand=True)
        self.canvas.bind('<ButtonPress-1>', self.on_canvas_press)
        self.canvas.bind('<B1-Motion>', self.on_canvas_drag)
        self.canvas.bind('<ButtonRelease-1>', self.on_canvas_release)
        self.canvas.bind('<Double-Button-1>', self.on_canvas_double)

        # Right: properties
        ttk.Label(self.right_frame, text='Element Properties').pack(pady=4)
        props = self.right_frame
        self.prop_type = ttk.Combobox(props, values=['text','image','rect','circle'])
        self.prop_type.pack(fill=tk.X, padx=6, pady=2)
        ttk.Label(props, text='Value (text or image path)').pack()
        self.prop_value = ttk.Entry(props)
        self.prop_value.pack(fill=tk.X, padx=6, pady=2)
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
        ttk.Button(props, text='Apply', command=self.apply_properties).pack(fill=tk.X, padx=6, pady=6)

        # Bottom: preview / generator
        gen_frame = ttk.Frame(self.right_frame)
        gen_frame.pack(side=tk.BOTTOM, fill=tk.X, pady=6)
        ttk.Button(gen_frame, text='Preview (as PNG)', command=self.preview_png).pack(fill=tk.X)
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
            try:
                self.project.import_asset(p)
            except Exception as e:
                print("Asset import failed:", e)
        self.refresh_assets()

    def refresh_assets(self):
        self.assets_listbox.delete(0, tk.END)
        if not self.project:
            return
        for a in self.project.list_assets():
            self.assets_listbox.insert(tk.END, os.path.basename(a))

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

    # ---------- Canvas interaction (drag/drop) ----------

    def on_canvas_press(self, event):
        if not self.current_template:
            return
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
        self.refresh_canvas()

    def on_canvas_release(self, event):
        if self.drag_data['item'] is not None:
            self.push_undo()
        self.drag_data = {'x':0,'y':0,'item':None,'index':None}

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
            ex, ey = el.x, el.y
            ew = el.w or 60
            eh = el.h or 30
            # for text, measure approximate bbox by size
            if el.type == 'text':
                ew = el.size * len(str(el.value)) // 2 + 10
                eh = el.size + 6
            # centre anchoring handling
            left = ex; top = ey
            right = ex + ew; bottom = ey + eh
            if left <= x <= right and top <= y <= bottom:
                return i
        return None

    # ---------- Properties panel ----------

    def fill_properties_from_selected(self):
        if not self.current_template or self.selected_element_index is None:
            # clear fields
            try:
                self.prop_type.set('')
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
        self.prop_size.delete(0, tk.END); self.prop_size.insert(0, str(el.size))
        self.prop_anchor.delete(0, tk.END); self.prop_anchor.insert(0, el.anchor)
        self.prop_rotate.delete(0, tk.END); self.prop_rotate.insert(0, str(el.rotate))

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
        self.push_undo()
        self.refresh_canvas()

    def pick_color(self):
        c = colorchooser.askcolor()[1]
        if c and self.current_template and self.selected_element_index is not None:
            self.current_template.elements[self.selected_element_index].color = c
            self.push_undo()
            self.refresh_canvas()

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
            # apply card size
            self.CARD_SIZE = (self.project.card_width, self.project.card_height)
            self.canvas.config(width=self.CARD_SIZE[0], height=self.CARD_SIZE[1])
        else:
            self.project_card_w.delete(0, tk.END); self.project_card_h.delete(0, tk.END)
        self.refresh_assets()
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
            ew = el.w or (el.size * len(str(el.value))//2 + 10) if el.type=='text' else (el.w or 40)
            eh = el.h or (el.size + 6) if el.type=='text' else (el.h or 30)
            self.canvas.create_rectangle(el.x-2, el.y-2, el.x+ew+2, el.y+eh+2, outline='blue', dash=(4,2))

    def draw_element_on_canvas(self, el: TemplateElement, selected: bool=False):
        # For text: use TK text
        if el.type == 'text':
            # placeholder rendering: show value literally (placeholders not expanded here)
            try:
                self.canvas.create_text(el.x, el.y, text=el.value, anchor='nw', font=(el.font, el.size), fill=el.color)
            except Exception:
                self.canvas.create_text(el.x, el.y, text=el.value, anchor='nw', fill=el.color)
        elif el.type == 'image':
            imgpath = el.value
            if imgpath and os.path.exists(imgpath):
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
                    self.canvas.create_text(el.x+4, el.y+4, text=os.path.basename(el.value) if el.value else 'image', anchor='nw')
            else:
                # simple rect placeholder
                self.canvas.create_rectangle(el.x, el.y, el.x+(el.w or 60), el.y+(el.h or 40), fill='gray')
                self.canvas.create_text(el.x+4, el.y+4, text=os.path.basename(el.value) if el.value else 'image', anchor='nw')
        elif el.type == 'rect':
            self.canvas.create_rectangle(el.x, el.y, el.x+(el.w or 60), el.y+(el.h or 30), fill=el.color)
        elif el.type == 'circle':
            r = el.w or 20
            self.canvas.create_oval(el.x-r, el.y-r, el.x+r, el.y+r, fill=el.color)
        else:
            self.canvas.create_text(el.x, el.y, text='?', anchor='nw')

    # ---------- Preview / Generate ----------

    def _render_template_to_image(self, template: Template, placeholders: Dict[str,str]) -> Image.Image:
        w, h = self.CARD_SIZE
        pil = Image.new('RGBA', (w, h), 'white')
        draw = ImageDraw.Draw(pil)
        for el in template.elements:
            if el.type == 'text':
                # replace placeholders in text
                text_val = str(el.value)
                for k, v in placeholders.items():
                    text_val = text_val.replace(f"{{{k}}}", v)
                try:
                    # try loading given font name (may be a font file path) or fallback
                    font = ImageFont.truetype(el.font, el.size)
                except Exception:
                    try:
                        font = ImageFont.truetype("arial.ttf", el.size)
                    except Exception:
                        font = ImageFont.load_default()
                draw.text((el.x, el.y), text_val, fill=el.color, font=font)
            elif el.type == 'image':
                imgpath = el.value
                # allow using assets base placeholder like {asset:xxx}
                if imgpath and imgpath.startswith('{asset:') and imgpath.endswith('}') and self.project:
                    inner = imgpath[7:-1]
                    imgpath = os.path.join(self.project.path, self.project.assets_dir, inner)
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
        if not self.current_template or not self.project:
            messagebox.showwarning('No template', 'Open a template in a project')
            return
        # use placeholders empty for preview
        pil = self._render_template_to_image(self.current_template, {})
        outpath = os.path.join(self.project.path, 'preview.png') if self.project else 'preview.png'
        pil.save(outpath)
        messagebox.showinfo('Preview saved', f'Preview saved to {outpath}')

    def _safe_filename(self, name: str) -> str:
        # simple slugify: keep alnum, dash, underscore
        name = name or ''
        name = re.sub(r'[^\w\-]+', '_', name)
        return name

    def generate_deck(self):
        if not self.current_template or not self.project:
            messagebox.showwarning('No template', 'Open a project and select a template')
            return
        csv_path = filedialog.askopenfilename(title='Select deck definition CSV', filetypes=[('CSV','*.csv;*.txt'), ('All','*.*')])
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
                        parts = line.split(';')
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
        out_folder = os.path.join(self.project.path, 'cards_output')
        os.makedirs(out_folder, exist_ok=True)

        # render each row
        for i, r in enumerate(rows, start=1):
            placeholders = {
                'name': r.get('nom_carte') or r.get('name') or '',
                'rank': r.get('rank', ''),
                'suit': r.get('suit', ''),
                'value': r.get('value', ''),
                'tag': r.get('tag', '')
            }
            pil = self._render_template_to_image(self.current_template, placeholders)
            safe = self._safe_filename(placeholders.get('name') or f'card_{i}')
            outname = f"{i:03d}_{safe}.png"
            outpath = os.path.join(out_folder, outname)
            try:
                pil.save(outpath)
            except Exception:
                try:
                    pil.convert('RGB').save(outpath)
                except Exception as e:
                    print('Failed to save', outpath, e)
        messagebox.showinfo('Generated', f'Generated {len(rows)} cards into {out_folder}')

# ---------- Run ----------

if __name__ == '__main__':
    # quick sanity checks
    try:
        root = tk.Tk()
    except Exception as e:
        print("Tkinter initialization failed:", e)
        raise
    app = EditorApp(root)
    root.mainloop()
