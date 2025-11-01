# -*- coding: utf-8 -*-
import cocos
from model import Table, Cell, Player
from controller import GameController
from view import DeployView, GameView
from cocos.director import director
import pyglet

# Gioco Open Lionheart by MoonDragon v.1.1
# Novembre 2025 - revisione n.3
# https://github.com/MoonDragon-MD/OpenLionheart

# Dipendenze richieste
# pip install pyglet cocos2d

class BannerLayer(cocos.layer.Layer):
    def __init__(self):
        super().__init__()
        try:
            banner = cocos.sprite.Sprite("banner_lionheart.png")
            banner.position = (400, 650)  # Posizione immagine
            self.add(banner)
            print("Banner caricato con successo")
        except Exception as e:
            print(f"Errore caricamento banner: {e}")
            self.add(cocos.layer.ColorLayer(100, 100, 100, 255))
        # Instruzioni a schermo
        instruction = cocos.text.Label(
            "Scegli una di queste modalità poi pigia Nuova partita",
            font_name='Arial',
            font_size=12,
            color=(255, 255, 255, 255),
            anchor_x='center',
            anchor_y='center',
            position=(400, 535) 
        )
        self.add(instruction, z=1)
        # Versione
        instruction = cocos.text.Label(
            "V. 1.1 Rev.3",
            font_name='Arial',
            font_size=12,
            color=(255, 255, 255, 255),
            anchor_x='center',
            anchor_y='center',
            position=(80, 80)  
        )
        self.add(instruction, z=1)
        # Crediti
        instruction = cocos.text.Label(
            "Creato da MoonDragon",
            font_name='Arial',
            font_size=12,
            color=(255, 255, 255, 255),
            anchor_x='center',
            anchor_y='center',
            position=(101, 60)  
        )
        self.add(instruction, z=1)

class AzureMenuItem(cocos.menu.MenuItem):
    def __init__(self, label, callback_func, *args, **kwargs):
        super().__init__(label, callback_func, *args, **kwargs)
        # Define font settings for azure color
        self.font_item = {'font_name': 'Arial', 'font_size': 20, 'color': (100, 100, 255, 255)}
        self.font_item_selected = {'font_name': 'Arial', 'font_size': 20, 'color': (100, 100, 255, 255)}

    def _create_label(self, selected=False):
        # Sostituire per creare etichetta con colore azzurro
        font = self.font_item_selected if selected else self.font_item
        return pyglet.text.Label(
            self.label,
            font_name=font['font_name'],
            font_size=font['font_size'],
            color=font['color'],
            anchor_x='center',
            anchor_y='center'
        )

class MenuLayer(cocos.menu.Menu):
    def __init__(self, gametitle):
        super().__init__(title=gametitle)
        self.controller = None
        self.advanced = False
        self.expert = False  # Nuova variabile per modo esperto
        self.bot_mode = False
        self.font_item = {'font_name': 'Arial', 'font_size': 20, 'color': (255, 255, 255, 255)}
        self.font_item_selected = {'font_name': 'Arial', 'font_size': 20, 'color': (128, 128, 128, 255)}
        items = [
            AzureMenuItem("Nuova partita", self.on_new_game),
            cocos.menu.MenuItem("Modo basico con bot", self.on_bot_mode),
            cocos.menu.MenuItem("Modo basico", self.on_basic),
            cocos.menu.MenuItem("Modo avanzato con bot", self.on_advanced_with_bot),
            cocos.menu.MenuItem("Modo avanzato", self.on_advanced),
            cocos.menu.MenuItem("Modo esperto con bot", self.on_expert_with_bot),  # Nuova opzione
            cocos.menu.MenuItem("Modo esperto", self.on_expert),  # Nuova opzione
            AzureMenuItem("Esci", self.on_quit),
        ]
        items[0].y = 100
        items[1].y = 50
        items[2].y = 0
        items[3].y = -50
        items[4].y = -100
        items[5].y = -150  # Posizione per "Modo esperto con bot"
        items[6].y = -200  # Posizione per "Modo esperto"
        items[7].y = -250  # Posizione per "Esci"
        self.create_menu(items)

    def on_basic(self):
        self.advanced = False
        self.expert = False
        self.bot_mode = False
        print("Modo basico selezionato, advanced=False, expert=False, bot_mode=False")

    def on_advanced(self):
        self.advanced = True
        self.expert = False
        self.bot_mode = False
        print("Modo avanzato selezionato, advanced=True, expert=False, bot_mode=False")

    def on_bot_mode(self):
        self.advanced = False
        self.expert = False
        self.bot_mode = True
        print("Modalità bot selezionata, advanced=False, expert=False, bot_mode=True")

    def on_advanced_with_bot(self):
        self.advanced = True
        self.expert = False
        self.bot_mode = True
        print("Modo avanzato con bot selezionato, advanced=True, expert=False, bot_mode=True")

    def on_expert(self):
        self.advanced = True
        self.expert = True
        self.bot_mode = False
        print("Modo esperto selezionato, advanced=True, expert=True, bot_mode=False")

    def on_expert_with_bot(self):
        self.advanced = True
        self.expert = True
        self.bot_mode = True
        print("Modo esperto con bot selezionato, advanced=True, expert=True, bot_mode=True")

    def on_new_game(self):
        print(f"Nuova partita avviata, modalità: {'esperta' if self.expert else 'avanzata' if self.advanced else 'basica'}, bot: {self.bot_mode}")
        self.controller = GameController(self.advanced, self.bot_mode, expert=self.expert)  # Passa expert
        director.replace(cocos.scene.Scene(DeployView(self.controller)))

    def on_quit(self):
        print("Uscita dal gioco")
        pyglet.app.exit()

if __name__ == "__main__":
    pyglet.resource.path = ['resources', '.']
    pyglet.resource.reindex()
    director.init(width=800, height=800, resizable=False)
    banner_layer = BannerLayer()
    menu = MenuLayer("Open Lionheart")
    main_scene = cocos.scene.Scene(banner_layer, menu)
    director.run(main_scene)
