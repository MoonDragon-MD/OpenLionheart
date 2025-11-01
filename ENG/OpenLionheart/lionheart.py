# -*- coding: utf-8 -*-
import cocos
from model import Table, Cell, Player
from controller import GameController
from view import DeployView, GameView
from cocos.director import director
import pyglet

# Open Lionheart game by MoonDragon v.1.1
# November 2025 - revision n.3
# https://github.com/MoonDragon-MD/OpenLionheart

# Dependencies required
# pip install pyglet cocos2d

class BannerLayer(cocos.layer.Layer):
    def __init__(self):
        super().__init__()
        try:
            banner = cocos.sprite.Sprite("banner_lionheart.png")
            banner.position = (400, 650)  # Image position
            self.add(banner)
            print("Banner successfully loaded")
        except Exception as e:
            print(f"Banner loading error: {e}")
            self.add(cocos.layer.ColorLayer(100, 100, 100, 255))
        # Instruction text
        instruction = cocos.text.Label(
            "Choose one of these modes then press the New Game",
            font_name='Arial',
            font_size=12,
            color=(255, 255, 255, 255),
            anchor_x='center',
            anchor_y='center',
            position=(400, 535) 
        )
        self.add(instruction, z=1)
        # Version text
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
        # Credit
        instruction = cocos.text.Label(
            "Created by MoonDragon",
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
        # Override to create label with azure color
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
        self.expert = False  # New variable for expert mode
        self.bot_mode = False
        self.font_item = {'font_name': 'Arial', 'font_size': 20, 'color': (255, 255, 255, 255)}
        self.font_item_selected = {'font_name': 'Arial', 'font_size': 20, 'color': (128, 128, 128, 255)}
        items = [
            AzureMenuItem("New Game", self.on_new_game),
            cocos.menu.MenuItem("Basic Bot Mode", self.on_bot_mode),
            cocos.menu.MenuItem("Basic mode", self.on_basic),
            cocos.menu.MenuItem("Advanced bot mode", self.on_advanced_with_bot),
            cocos.menu.MenuItem("Advanced mode", self.on_advanced),
            cocos.menu.MenuItem("Expert bot mode", self.on_expert_with_bot),  # New option
            cocos.menu.MenuItem("Expert mode", self.on_expert),  # New option
            AzureMenuItem("Exit", self.on_quit),
        ]
        items[0].y = 100
        items[1].y = 50
        items[2].y = 0
        items[3].y = -50
        items[4].y = -100
        items[5].y = -150  
        items[6].y = -200  
        items[7].y = -250  # Position exit text
        self.create_menu(items)

    def on_basic(self):
        self.advanced = False
        self.expert = False
        self.bot_mode = False
        print("Selected basic mode, advanced=False, expert=False, bot_mode=False")

    def on_advanced(self):
        self.advanced = True
        self.expert = False
        self.bot_mode = False
        print("Selected Advanced mode, advanced=True, expert=False, bot_mode=False")

    def on_bot_mode(self):
        self.advanced = False
        self.expert = False
        self.bot_mode = True
        print("Selected bot mode, advanced=False, expert=False, bot_mode=True")

    def on_advanced_with_bot(self):
        self.advanced = True
        self.expert = False
        self.bot_mode = True
        print("Selected Advanced bot mode, advanced=True, expert=False, bot_mode=True")

    def on_expert(self):
        self.advanced = True
        self.expert = True
        self.bot_mode = False
        print("Selected Expert mode, advanced=True, expert=True, bot_mode=False")

    def on_expert_with_bot(self):
        self.advanced = True
        self.expert = True
        self.bot_mode = True
        print("Selected Expert bot mode, advanced=True, expert=True, bot_mode=True")

    def on_new_game(self):
        print(f"New game started, mode: {'esperta' if self.expert else 'avanzata' if self.advanced else 'basica'}, bot: {self.bot_mode}")
        self.controller = GameController(self.advanced, self.bot_mode, expert=self.expert)  # Passa to Expert
        director.replace(cocos.scene.Scene(DeployView(self.controller)))

    def on_quit(self):
        print("Exit from the game")
        pyglet.app.exit()

if __name__ == "__main__":
    pyglet.resource.path = ['resources', '.']
    pyglet.resource.reindex()
    director.init(width=800, height=800, resizable=False)
    banner_layer = BannerLayer()
    menu = MenuLayer("Open Lionheart")
    main_scene = cocos.scene.Scene(banner_layer, menu)
    director.run(main_scene)
