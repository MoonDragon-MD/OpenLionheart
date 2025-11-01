# -*- coding: utf-8 -*-
import cocos
from model import Table, Cell, Player
import cocos.tiles
from cocos.director import director
import pyglet
from pyglet.window import mouse
from units import *
import controller
import random
from units import unit  # Importa la classe unit
import pyglet.clock # per ritardare entrata in gioco

# TableView per visualizzare il tavolo da gioco
class TableView(cocos.layer.Layer):
    def __init__(self, tablero):
        super().__init__()
        self.name = 'TableView'
        self.tablero = tablero
        self.cell_size = 67
        self.offset_x = 100
        self.offset_y = 186
        self.cells = {}

        # Crea le celle di sfondo
        for i in range(self.tablero.rows):
            for j in range(self.tablero.columns):
                cell = self.tablero.cell_list[i][j]
                sprite = cocos.sprite.Sprite("cuadrado.png", position=(
                    self.offset_x + j * self.cell_size + self.cell_size / 2,
                    self.offset_y + i * self.cell_size + self.cell_size / 2
                ))
                self.add(sprite, z=0)
                self.cells[(i, j)] = sprite

        # Aggiungi le unità esistenti
        for (i, j), unit in self.tablero.units.items():
            unit.posx = self.cells[(i, j)].position[0]
            unit.posy = self.cells[(i, j)].position[1]
            unit.scale = min(self.cell_size / unit.width, self.cell_size / unit.height) if unit.width > 0 and unit.height > 0 else 1.0
            unit.update_position()
            self.add(unit, z=1)
            print(f"Aggiunto sprite unità {unit.__class__.__name__} a ({i}, {j}), posizione: ({unit.posx}, {unit.posy}), scala: {unit.scale}")
        print(f"TableView inizializzato con {self.tablero.rows}x{self.tablero.columns} celle")

    def update_cell(self, i, j):
        print(f"TableView: Aggiorno cella ({i}, {j})")
        if (i, j) in self.tablero.units:
            unit_instance = self.tablero.units[(i, j)]
            unit_instance.posx = self.cells[(i, j)].position[0]
            unit_instance.posy = self.cells[(i, j)].position[1]
            unit_instance.scale = min(self.cell_size / unit_instance.width, self.cell_size / unit_instance.height) if unit_instance.width > 0 and unit_instance.height > 0 else 1.0
            unit_instance.visible = True
            unit_instance.opacity = 255
            unit_instance.update_position()
            if unit_instance.parent != self:
                if unit_instance.parent:
                    unit_instance.parent.remove(unit_instance)
                    print(f"TableView: Rimosso parent precedente {unit_instance.parent.__class__.__name__ if unit_instance.parent else 'None'} per unità {unit_instance.__class__.__name__} a ({i}, {j})")
                self.add(unit_instance, z=1)
                print(f"TableView: Aggiunto sprite unità {unit_instance.__class__.__name__} a ({i}, {j}), posizione: ({unit_instance.posx}, {unit_instance.posy}), scala: {unit_instance.scale}, visibile: {unit_instance.visible}, opacità: {unit_instance.opacity}")
            else:
                print(f"TableView: Unità {unit_instance.__class__.__name__} già presente a ({i}, {j}), posizione aggiornata")
        else:
            # Rimuovi sprite obsolete
            for child in list(self.children):
                sprite, z = child
                if isinstance(sprite, unit) and sprite.i == i and sprite.j == j:
                    self.remove(sprite)
                    sprite.visible = False
                    sprite.opacity = 0
                    print(f"TableView: Rimossa sprite obsoleta da ({i}, {j}), visibile: {sprite.visible}, opacità: {sprite.opacity}")

# Livello interfaccia utente
class UILayer(cocos.layer.Layer):
    is_event_handler = True

    def __init__(self, is_deploy=False, current_player=None):
        super().__init__()
        self.name = 'UILayer'
        self.text_background = cocos.layer.ColorLayer(0, 0, 0, 128, width=300, height=50)
        self.text_background.position = (500, 45)
        self.add(self.text_background, z=30)
        print(f"Text background aggiunto a {self.text_background.position}, z=30, visibile: {self.text_background.visible}")

        text = "Player 1 deploying" if is_deploy else f"Turno: {current_player.Name}" if current_player else ""
        self.text = cocos.text.Label(
            text, font_size=16, color=(255, 255, 255, 255), anchor_x='center', anchor_y='center'
        )
        self.text.position = (650, 60)
        self.add(self.text, z=31)
        print(f"Testo renderizzato: {self.text.element.text} at {self.text.position}, z=31, visibile: {self.text.visible}")

        self.end_turn_button = cocos.sprite.Sprite(
            pyglet.image.SolidColorImagePattern((100, 100, 255, 255)).create_image(120, 50)
        )
        self.end_turn_button.position = (700, 100)
        self.end_turn_button.visible = not is_deploy
        self.add(self.end_turn_button, z=30)
        print(f"Pulsante Fine Turno aggiunto a {self.end_turn_button.position}, z=30, visibile: {self.end_turn_button.visible}")

        self.end_turn_label = cocos.text.Label(
            "Fine Turno", font_size=16, color=(255, 255, 255, 255), anchor_x='center', anchor_y='center'
        )
        self.end_turn_label.position = (700, 100)
        self.end_turn_label.visible = not is_deploy
        self.add(self.end_turn_label, z=31)
        print(f"Etichetta Fine Turno aggiunta a {self.end_turn_label.position}, z=31, visibile: {self.end_turn_label.visible}")

        self.menu_button = cocos.sprite.Sprite(
            pyglet.image.SolidColorImagePattern((100, 100, 255, 255)).create_image(120, 50)
        )
        self.menu_button.position = (650, 20)
        self.add(self.menu_button, z=30)
        print(f"Pulsante Torna al menù aggiunto a {self.menu_button.position}, z=30, visibile: {self.menu_button.visible}")

        self.menu_label = cocos.text.Label(
            "Torna al menù", font_size=12, color=(255, 255, 255, 255), anchor_x='center', anchor_y='center'
        )
        self.menu_label.position = (650, 20)
        self.add(self.menu_label, z=31)
        print(f"Etichetta Torna al menù aggiunta a {self.menu_label.position}, z=31, visibile: {self.menu_label.visible}")
    def update_text(self, text):
        self.text.element.text = text
        print(f"Testo aggiornato: {self.text.element.text}")

    def show_end_turn(self, show):
        self.end_turn_button.visible = show
        self.end_turn_label.visible = show
        print(f"Pulsante Fine Turno aggiornato, visibile: {self.end_turn_button.visible}")

    def on_mouse_press(self, x, y, buttons, modifiers):
        if buttons & mouse.LEFT:
            # Controllo pulsante Fine Turno
            if (self.end_turn_button.visible and
                self.end_turn_button.x - 60 <= x <= self.end_turn_button.x + 60 and
                self.end_turn_button.y - 25 <= y <= self.end_turn_button.y + 25):
                print("Pulsante Fine Turno cliccato")
                return "end_turn"
            
            # Controllo pulsante Menu
            if (self.menu_button.x - 60 <= x <= self.menu_button.x + 60 and
                self.menu_button.y - 25 <= y <= self.menu_button.y + 25):
                print("Pulsante Menu cliccato")
                return "menu"
        return None

# Modalità DeployView
class DeployView(cocos.layer.Layer):
    is_event_handler = True

    def __init__(self, controller):
        super().__init__()
        self.name = 'DeployView'
        print("Inizializzo Deploy")
        self.controller = controller
        self.table = TableView(self.controller.tablero)
        self.add(self.table, z=0)
        self.ui_layer = UILayer(is_deploy=True)
        self.add(self.ui_layer, z=10)
        self.unitsDeployed = 0
        self.units = []
        self.playerDeploy = self.controller.player1
        print(f"playerDeploy impostato: {self.playerDeploy.Name}, ID: {id(self.playerDeploy)}, player1 ID: {id(self.controller.player1)}")
        self.selected = None
        self.deploy_area = cocos.layer.Layer()
        self.deploy_area.position = (20, 20) 
        self.add(self.deploy_area, z=5)
        self.deploy_cells = []
        self.bot_deployed = False

        if not self.controller.advanced:
            self.on_basic_mode()
        else:
            print(f"Inizializzazione schieramento avanzato, playerDeploy: {self.playerDeploy.Name}")
            self.create_units(self.controller.player1, 1)
            # Crea unità per Player 2 anche in modalità non-bot
            self.create_units(self.controller.player2, 3)
            print(f"Unità totali in deploy_cells: {[c['unit'].owner.Name for c in self.deploy_cells]}")
            self.show_deploy_cells()
            self.ui_layer.update_text(f"{self.playerDeploy.Name} schierare")
            print(f"playerDeploy inizializzato: {self.playerDeploy.Name}, player1: {self.controller.player1.Name}")

    def register_event_handlers(self):
        # Non necessario, gli eventi sono gestiti automaticamente con is_event_handler
        print("Gestori di eventi attivi per DeployView (gestiti automaticamente)")

    def remove_all_handlers(self):
        # Disattiva semplicemente il layer
        self.is_event_handler = False
        print("Gestori di eventi disattivati per DeployView")

    def show_deploy_cells(self):
        print(f"Mostro celle schierabili per {self.playerDeploy.Name}")
        self.controller.tablero.clear_activated()
        rows = [0, 1] if self.playerDeploy == self.controller.player1 else [6, 7]  # Conferma righe
        activated_cells = []
        for i in rows:
            for j in range(self.controller.tablero.columns):
                cell = self.controller.tablero.cell_at(i, j)
                if cell and not cell.isUnit:
                    cell.activate()
                    activated_cells.append((i, j))
        print(f"Celle attivate: righe {rows}, celle: {activated_cells}")
        
    def place_unit(self, unit, row, col):
        print(f"Posizionamento unità {unit.__class__.__name__} a ({row}, {col})")
        self.controller.tablero.deploy_unit(unit, row, col)
        self.units.remove(unit)
        if unit.parent == self.deploy_area:
            self.deploy_area.remove(unit)
            print(f"Rimossa unità da deploy_area")
        else:
            self.remove(unit)
        self.table.update_cell(row, col)
        cell = self.controller.tablero.cell_at(row, col)
        print(f"Cella ({row}, {col}) contiene unità: {cell.isUnit}, unità: {cell.__class__.__name__ if cell.isUnit else None}")
        if len(self.units) == 0:
            print("Tutte le unità posizionate, passo allo stato successivo")
            self.parent.next_state()

    def create_units(self, player, orientation):
        print(f"Creo unità per {player.Name}, modo esperto: {self.controller.expert}")
        base_x, base_y = 30, 18  # Posizione blocco unità da mettere sul tavolo da gioco
        cell_size = 67
        units = [
            soldier(0, 0, base_x, base_y, orientation, 4, player, table=self.controller.tablero),
            soldier(0, 1, base_x + cell_size, base_y, orientation, 4, player, table=self.controller.tablero),
            soldier(0, 2, base_x + 2 * cell_size, base_y, orientation, 4, player, table=self.controller.tablero),
            soldier(0, 3, base_x + 3 * cell_size, base_y, orientation, 4, player, table=self.controller.tablero),
            soldier(0, 5, base_x + 5 * cell_size, base_y, orientation, 4, player, table=self.controller.tablero),
            soldier(1, 0, base_x, base_y + cell_size, orientation, 4, player, table=self.controller.tablero),
            archer(1, 1, base_x + cell_size, base_y + cell_size, orientation, 4, player, table=self.controller.tablero),
            archer(1, 2, base_x + 2 * cell_size, base_y + cell_size, orientation, 4, player, table=self.controller.tablero),
            heavy_infantry(1, 3, base_x + 3 * cell_size, base_y + cell_size, orientation, 2, player, table=self.controller.tablero),
            heavy_infantry(1, 4, base_x + 4 * cell_size, base_y + cell_size, orientation, 2, player, table=self.controller.tablero),
            knight(2, 0, base_x, base_y + 2 * cell_size, orientation, 2, player, table=self.controller.tablero),
            king(2, 1, base_x + cell_size, base_y + 2 * cell_size, orientation, player, table=self.controller.tablero),
            peasant(2, 3, base_x + 3 * cell_size, base_y + 2 * cell_size, orientation, 4, player, table=self.controller.tablero),
            peasant(2, 4, base_x + 4 * cell_size, base_y + 2 * cell_size, orientation, 4, player, table=self.controller.tablero),
            mercenary(2, 5, base_x + 5 * cell_size, base_y + 2 * cell_size, orientation, 2, player, table=self.controller.tablero),
        ]
        if self.controller.expert:
            units.extend([
                crossbowman(1, 5, base_x + 5 * cell_size, base_y + cell_size, orientation, 2, player, table=self.controller.tablero),
                shield_wall(2, 2, base_x + 2 * cell_size, base_y + 2 * cell_size, orientation, 4, player, table=self.controller.tablero),
                shield_wall(0, 4, base_x + 4 * cell_size, base_y, orientation, 4, player, table=self.controller.tablero),
            ])
        self.units.extend(units)
        z_order = 3 if player == self.controller.player1 else 2
        for unit in units:
            i, j = unit.i, unit.j
            unit.posx = base_x + j * cell_size
            unit.posy = base_y + i * cell_size
            screen_x = unit.posx + self.deploy_area.position[0]
            screen_y = unit.posy + self.deploy_area.position[1]
            print(f"Creata unità {unit.__class__.__name__} a grid ({i}, {j}), local_pos=({unit.posx}, {unit.posy}), screen_pos=({screen_x}, {screen_y}), hitbox=({screen_x - cell_size/2:.1f}, {screen_y - cell_size/2:.1f}, {screen_x + cell_size/2:.1f}, {screen_y + cell_size/2:.1f}), proprietario: {player.Name}, z={z_order}")
            self.deploy_area.add(unit, z=z_order)
            unit.update_position()
            self.deploy_cells.append({
                'unit': unit,
                'x': unit.posx,
                'y': unit.posy,
                'i': i,
                'j': j
            })
            player.units.append(unit)

    def deploy(self, x, y):
        print(f"Deploy chiamato con coordinate assolute=({x}, {y})")
        cell = self.get_deploy_cell(x - self.deploy_area.position[0], y - self.deploy_area.position[1])
        print(f"Coordinate relative passate a get_deploy_cell=({x - self.deploy_area.position[0]:.1f}, {y - self.deploy_area.position[1]:.1f})")
        if cell and not self.selected:
            self.select(cell['unit'])
        elif self.selected:
            cell = self.controller.tablero.get_cell(x, y)
            if cell and cell.activated and not cell.isUnit:
                print(f"Tentativo di schierare {self.selected.__class__.__name__} a ({cell.i}, {cell.j})")
                if self.controller.tablero.deploy_unit(cell.i, cell.j, self.selected):
                    self.deploy_cells = [c for c in self.deploy_cells if c['unit'] != self.selected]
                    self.units.remove(self.selected)
                    self.unitsDeployed += 1
                    self.table.update_cell(cell.i, cell.j)
                    print(f"Unità {self.selected.__class__.__name__} schierata a ({cell.i}, {cell.j}), presente in tablero.units: {(cell.i, cell.j) in self.controller.tablero.units}")
                    self.selected.deselect()
                    self.selected = None
                    if all(u.owner != self.playerDeploy for u in self.units):
                        if self.playerDeploy == self.controller.player1:
                            print(f"Schieramento di {self.playerDeploy.Name} completato")
                            self.playerDeploy = self.controller.player2
                            self.unitsDeployed = 0
                            self.show_deploy_cells()
                            self.ui_layer.update_text(f"{self.playerDeploy.Name} schierare")
                            if self.controller.bot_mode:
                                print("Avvio schieramento bot")
                                self.bot_deploy()
                        else:
                            print("Schieramento completato per entrambi i giocatori")
                            self.ui_layer.update_text("Fine schieramento")
                            self.controller.end_deployment()
                            self.controller.tablero.clear_activated()
                            # Log delle unità schierate
                            print(f"Unità in tablero.units dopo deploy: {[(i, j, u.__class__.__name__, u.owner.Name) for (i, j), u in self.controller.tablero.units.items()]}")
                            self.is_event_handler = False
                            director.replace(cocos.scene.Scene(GameView(self.controller)))
                            print("Transizione a GameView completata")
                else:
                    print(f"Schieramento di {self.selected.__class__.__name__} fallito a ({cell.i}, {cell.j})")
                    self.selected.deselect()
                    self.selected = None
        return
                
    def bot_deploy(self):
        if self.bot_deployed:
            return
        print("Bot schiera unità")
        rows = [6, 7]
        available_cells = [(i, j) for i in rows for j in range(self.controller.tablero.columns) if (i, j) not in self.controller.tablero.units]
        random.shuffle(available_cells)
        king_pos = None
        shield_wall_positions = []

        # Schiera il Re
        king = next((cell['unit'] for cell in self.deploy_cells if cell['unit'].isKing and cell['unit'].owner == self.controller.player2), None)
        if king:
            row_7_cells = [(7, j) for j in range(self.controller.tablero.columns) if (7, j) in available_cells]
            row_6_cells = [(6, j) for j in range(self.controller.tablero.columns) if (6, j) in available_cells]
            if row_7_cells:
                king_pos = (7, 4) if (7, 4) in row_7_cells else random.choice(row_7_cells)
            elif row_6_cells:
                king_pos = random.choice(row_6_cells)
            else:
                print("Errore: nessuna cella disponibile per schierare il re del bot")
                return
            if king_pos and self.controller.tablero.deploy_unit(king_pos[0], king_pos[1], king):
                self.deploy_cells = [c for c in self.deploy_cells if c['unit'] != king]
                self.units.remove(king)
                self.unitsDeployed += 1
                available_cells.remove(king_pos)
                self.table.update_cell(king_pos[0], king_pos[1])
                print(f"Bot: Re schierato a {king_pos}")

        # In modalità esperto, schiera Muri di scudi e posiziona Arcieri/Balestrieri dietro
        if self.controller.expert:
            shield_walls = [cell['unit'] for cell in self.deploy_cells if cell['unit'].__class__.__name__ == "shield_wall" and cell['unit'].owner == self.controller.player2]
            for shield_wall in shield_walls:
                front_cells = [(6, j) for j in range(self.controller.tablero.columns) if (6, j) in available_cells]
                if front_cells:
                    pos = random.choice(front_cells)
                    if self.controller.tablero.deploy_unit(pos[0], pos[1], shield_wall):
                        shield_wall.setOrientation(3)  # Orientamento verso il basso
                        self.deploy_cells = [c for c in self.deploy_cells if c['unit'] != shield_wall]
                        self.units.remove(shield_wall)
                        self.unitsDeployed += 1
                        available_cells.remove(pos)
                        shield_wall_positions.append(pos)
                        self.table.update_cell(pos[0], pos[1])
                        print(f"Bot: Muro di scudi schierato a {pos}")

            # Schiera Arcieri e Balestrieri dietro i Muri di scudi
            ranged_units = [cell['unit'] for cell in self.deploy_cells if cell['unit'].__class__.__name__ in ["archer", "crossbowman"] and cell['unit'].owner == self.controller.player2]
            for ranged_unit in ranged_units:
                protected_cells = []
                for sw_pos in shield_wall_positions:
                    back_pos = (7, sw_pos[1])  # Cella dietro il Muro di scudi (riga 7, stessa colonna)
                    if back_pos in available_cells:
                        protected_cells.append(back_pos)
                pos = protected_cells[0] if protected_cells else random.choice(available_cells) if available_cells else None
                if pos and self.controller.tablero.deploy_unit(pos[0], pos[1], ranged_unit):
                    ranged_unit.setOrientation(3)  # Orientamento verso il basso
                    self.deploy_cells = [c for c in self.deploy_cells if c['unit'] != ranged_unit]
                    self.units.remove(ranged_unit)
                    self.unitsDeployed += 1
                    available_cells.remove(pos)
                    self.table.update_cell(pos[0], pos[1])
                    print(f"Bot: {ranged_unit.__class__.__name__} schierato a {pos}")
        else:
            # Schiera Arcieri normalmente (modalità non esperto)
            archers = [cell['unit'] for cell in self.deploy_cells if cell['unit'].__class__.__name__ == "archer" and cell['unit'].owner == self.controller.player2]
            archer_positions = [(6, j) for j in range(self.controller.tablero.columns) if (6, j) in available_cells]
            random.shuffle(archer_positions)
            for archer in archers:
                if archer_positions:
                    archer_pos = archer_positions.pop(0)
                    if self.controller.tablero.deploy_unit(archer_pos[0], archer_pos[1], archer):
                        self.deploy_cells = [c for c in self.deploy_cells if c['unit'] != archer]
                        self.units.remove(archer)
                        self.unitsDeployed += 1
                        available_cells.remove(archer_pos)
                        self.table.update_cell(archer_pos[0], archer_pos[1])
                        print(f"Bot: Arciere schierato a {archer_pos}")

        # Schiera le unità rimanenti vicino al Re
        if king_pos:
            adjacent_cells = [(i, j) for i in [6, 7] for j in range(self.controller.tablero.columns) if (i, j) in available_cells and abs(i) + abs(j - king_pos[1]) <= 3]
        else:
            adjacent_cells = []
        random.shuffle(adjacent_cells)
        for cell in self.deploy_cells[:]:
            if cell['unit'].owner != self.controller.player2:
                continue
            unit_instance = cell['unit']
            pos = adjacent_cells.pop(0) if adjacent_cells else random.choice(available_cells) if available_cells else None
            if pos and self.controller.tablero.deploy_unit(pos[0], pos[1], unit_instance):
                self.units.remove(unit_instance)
                self.unitsDeployed += 1
                available_cells.remove(pos)
                self.deploy_cells = [c for c in self.deploy_cells if c['unit'] != unit_instance]
                self.table.update_cell(pos[0], pos[1])
                print(f"Bot: Unità {unit_instance.__class__.__name__} schierata a {pos}")

        self.bot_deployed = True
        self.ui_layer.update_text("Finished deploying")
        self.controller.end_deployment()
        self.controller.tablero.clear_activated()
        self.is_event_handler = False
        # Verifica che le unità del Player 1 siano presenti
        player1_units = [(i, j) for (i, j), u in self.controller.tablero.units.items() if u.owner == self.controller.player1]
        print(f"Unità Player 1: {player1_units}")
        director.replace(cocos.scene.Scene(GameView(self.controller)))
        print("Transizione a GameView")

    def get_deploy_cell(self, x, y):
        cell_size = 67
        print(f"Ricerca cella di schieramento a screen=({x:.1f}, {y:.1f})")
        for cell in sorted(self.deploy_cells, key=lambda c: c['unit'].owner == self.playerDeploy, reverse=True):
            if cell['unit'].owner != self.playerDeploy:
                print(f"Ignorata unità con proprietario {cell['unit'].owner.Name}, attesa {self.playerDeploy.Name}")
                continue
            screen_x = cell['x'] + self.deploy_area.position[0]
            screen_y = cell['y'] + self.deploy_area.position[1]
            print(f"Controllo unità a grid ({cell['i']}, {cell['j']}), hitbox=({screen_x - cell_size/2:.1f}, {screen_y - cell_size/2:.1f}, {screen_x + cell_size/2:.1f}, {screen_y + cell_size/2:.1f})")
            if (screen_x - cell_size/2 <= x <= screen_x + cell_size/2 and
                screen_y - cell_size/2 <= y <= screen_y + cell_size/2):
                print(f"Trovata cella di schieramento a grid ({cell['i']}, {cell['j']}), screen=({x:.1f}, {y:.1f}), unit_pos=({screen_x}, {screen_y}), proprietario: {cell['unit'].owner.Name}, colore: {cell['unit'].color}")
                return cell
        print(f"Nessuna cella di schieramento trovata a screen=({x:.1f}, {y:.1f})")
        return None

    def on_mouse_release(self, x, y, buttons, modifiers):
        if not self.is_running:
            print("Ignorato clic: DeployView non è più attivo")
            return
        print(f"Mouse rilasciato a ({x}, {y}), pulsante: {buttons}")
        if self.controller.phase != "deployment":
            print(f"Ignorato clic: fase corrente {self.controller.phase}, attesa 'deployment'")
            return
        if buttons & mouse.LEFT:
            ui_action = self.ui_layer.on_mouse_press(x, y, buttons, modifiers)
            if ui_action == "menu":
                try:
                    from lionheart import MenuLayer, BannerLayer
                    banner_layer = BannerLayer()
                    menu = MenuLayer("Open Lionheart")
                    self.is_event_handler = False
                    director.replace(cocos.scene.Scene(banner_layer, menu))
                    print("Tornato al menù principale con successo")
                except Exception as e:
                    print(f"Errore durante la transizione al menù principale: {str(e)}")
                return
            self.deploy(x, y)

    def select(self, unit):
        if self.selected:
            self.selected.deselect()
        self.selected = unit
        self.selected.select()
        print(f"Unità selezionata a ({unit.i}, {unit.j}) con {unit.soldiers if not unit.isKing else 1} soldati")

    def on_basic_mode(self):
        print("Schieramento automatico per modalità base")
        print(f"Controller tablero: {self.controller.tablero.__class__.__name__ if self.controller.tablero else 'None'}")
        self.controller.player1.units.clear()
        self.controller.player2.units.clear()
        self.controller.tablero.units.clear()

        # Deploy Giocatore 1
        for i in range(5):
            unit_instance = soldier(1, 2+i, None, None, 1, 4, self.controller.player1, table=self.controller.tablero)
            if self.controller.tablero.deploy_unit(1, 2+i, unit_instance):
                self.controller.player1.units.append(unit_instance)
                self.table.update_cell(1, 2+i)
                print(f"Schierata unità soldier a (1, {2+i}), posizione: ({unit_instance.posx}, {unit_instance.posy}), visibile: {unit_instance.visible}, opacità: {unit_instance.opacity}")

        unit_types_p1 = [
            (king, 0, 4, 1, None),
            (knight, 0, 3, 1, 2),
            (knight, 0, 5, 1, 2),
            (archer, 0, 2, 1, 4),
            (archer, 0, 6, 1, 4),
        ]
        for unit_type, i, j, orientation, soldiers in unit_types_p1:
            if unit_type == king:
                unit_instance = unit_type(i, j, None, None, orientation, self.controller.player1, table=self.controller.tablero)
            else:
                unit_instance = unit_type(i, j, None, None, orientation, soldiers, self.controller.player1, table=self.controller.tablero)
            if self.controller.tablero.deploy_unit(i, j, unit_instance):
                self.controller.player1.units.append(unit_instance)
                self.table.update_cell(i, j)
                print(f"Schierata {unit_type.__name__} a ({i}, {j}), posizione: ({unit_instance.posx}, {unit_instance.posy}), soldati: {unit_instance.soldiers}, visibile: {unit_instance.visible}, opacità: {unit_instance.opacity}")
            else:
                print(f"Errore: schieramento {unit_type.__name__} a ({i}, {j})")

        # Deploy Player 2
        for i in range(5):
            unit_instance = soldier(6, 2+i, None, None, 3, 4, self.controller.player2, table=self.controller.tablero)
            if self.controller.tablero.deploy_unit(6, 2+i, unit_instance):
                self.controller.player2.units.append(unit_instance)
                self.table.update_cell(6, 2+i)
                print(f"Schierata unità soldier a (6, {2+i}), posizione: ({unit_instance.posx}, {unit_instance.posy}), visibile: {unit_instance.visible}, opacità: {unit_instance.opacity}")
            else:
                print(f"Errore: schieramento soldier a (6, {2+i})")

        unit_types_p2 = [
            (king, 7, 4, 3, None),
            (knight, 7, 3, 3, 2),
            (knight, 7, 5, 3, 2),
            (archer, 7, 2, 3, 4),
            (archer, 7, 6, 3, 4),
        ]
        for unit_type, i, j, orientation, soldiers in unit_types_p2:
            if unit_type == king:
                unit_instance = unit_type(i, j, None, None, orientation, self.controller.player2, table=self.controller.tablero)
            else:
                unit_instance = unit_type(i, j, None, None, orientation, soldiers, self.controller.player2, table=self.controller.tablero)
            if self.controller.tablero.deploy_unit(i, j, unit_instance):
                self.controller.player2.units.append(unit_instance)
                self.table.update_cell(i, j)
                print(f"Schierata {unit_type.__name__} a ({i}, {j}), posizione: ({unit_instance.posx}, {unit_instance.posy}), soldati: {unit_instance.soldiers}, visibile: {unit_instance.visible}, opacità: {unit_instance.opacity}")
            else:
                print(f"Errore: schieramento {unit_type.__name__} a ({i}, {j})")

        # Verifica deployment
        print(f"Player 1 units: {len(self.controller.player1.units)} ({[(u.i, u.j, u.__class__.__name__, u.soldiers, u.movements) for u in self.controller.player1.units]})")
        print(f"Player 2 units: {len(self.controller.player2.units)} ({[(u.i, u.j, u.__class__.__name__, u.soldiers, u.movements) for u in self.controller.player2.units]})")
        self.controller.current_player = self.controller.player1
        self.controller.next_phase()
        self.controller.end_deployment()
        self.controller.tablero.clear_activated()
        self.ui_layer.update_text(f"Turno: {self.controller.current_player.Name}")
        self.ui_layer.show_end_turn(True)
        self.is_event_handler = False
        pyglet.clock.schedule_once(lambda dt: director.replace(cocos.scene.Scene(GameView(self.controller))), 0.5)
        print("Programmata transizione a GameView")

# Sistema Dadi
class DiceLayer(cocos.layer.Layer):
    is_event_handler = True

    def __init__(self, controller):
        super().__init__()
        self.name = 'DiceLayer'
        self.controller = controller
        self.position = (0, 0)
        self.enabled = True  # Sempre abilitato per test
        self.dice_count = 2  # Base impostato a 2 dadi
        self.dice_results = []
        self.batch = pyglet.graphics.Batch()

        self.roll_button = cocos.sprite.Sprite(
            pyglet.image.SolidColorImagePattern((100, 100, 255, 255)).create_image(120, 50)
        )
        self.roll_button.position = (466, 164)
        self.add(self.roll_button, z=30)
        print(f"Pulsante Tira dadi aggiunto a {self.roll_button.position}, z=30, visibile: {self.roll_button.visible}")

        self.button_label = cocos.text.Label(
            "Tira dadi", font_size=14, x=456, y=164, color=(255, 255, 255, 255), anchor_x='center', anchor_y='center'
        )
        self.add(self.button_label, z=31)
        print(f"Etichetta Tira dadi aggiunta a ({self.button_label.x}, {self.button_label.y}), z=31, visibile: {self.button_label.visible}")

        self.dice_sprites = []
        positions = [(436, 114), (496, 114), (436, 54), (496, 54)]
        faces = ["axe.png", "arrow.png", "soldier_scream.png"]
        for i, pos in enumerate(positions):
            face = random.choice(faces)
            try:
                sprite = cocos.sprite.Sprite(
                    pyglet.resource.image(face),
                    position=pos
                )
                sprite.scale = 60 / max(sprite.image.width, sprite.image.height)
            except pyglet.resource.ResourceNotFoundException:
                print(f"Errore: immagine {face} non trovata!")
                sprite = cocos.sprite.Sprite(
                    pyglet.image.SolidColorImagePattern((255, 0, 0, 255)).create_image(60, 60),
                    position=pos
                )
                sprite.scale = 1.0
            sprite.visible = True
            sprite.opacity = 255
            sprite.batch = self.batch
            self.add(sprite, z=30)
            self.dice_sprites.append(sprite)
            print(f"Dado {i+1} inizializzato a {pos} con {face}, visibile: {sprite.visible}, opacità: {sprite.opacity}")

    def hide_dice(self, dt=None):
        for i, sprite in enumerate(self.dice_sprites):
            sprite.visible = False
            sprite.opacity = 0
            print(f"Dado {i+1} visibile: {sprite.visible}, opacità: {sprite.opacity}")
        print(f"Dadi nascosti: {self.dice_count} dadi, opacità: {[s.opacity for s in self.dice_sprites]}")

    def set_enabled(self, enabled, dice_count=4, hide_dice=True):
        self.enabled = enabled
        self.dice_count = min(dice_count, len(self.dice_sprites))
        self.roll_button.image = pyglet.image.SolidColorImagePattern(
            (100, 100, 255, 255) if enabled else (128, 128, 128, 255)
        ).create_image(100, 40)
        self.button_label.visible = True
        if hide_dice:
            self.hide_dice()  # Assicura che i dadi siano nascosti solo se richiesto
        print(f"Pulsante Tira dadi: {'abilitato' if enabled else 'disabilitato'}, {self.dice_count} dadi")

    def roll_dice(self):
        faces = ["axe.png", "arrow.png", "soldier_scream.png"]
        results = [random.choice(faces) for _ in range(self.dice_count)]
        self.dice_results = [1 if face == "axe.png" else 2 if face == "arrow.png" else 3 for face in results]
        for i, sprite in enumerate(self.dice_sprites):
            sprite.visible = i < self.dice_count
            sprite.opacity = 255 if i < self.dice_count else 0
            if i < self.dice_count:
                try:
                    sprite.image = pyglet.resource.image(results[i])
                    sprite.scale = 60 / max(sprite.image.width, sprite.image.height)
                    sprite.position = (436 + (i % 2) * 60, 114 - (i // 2) * 60)
                    sprite.batch = self.batch
                    print(f"Dado {i+1}: {results[i]}, posizione: {sprite.position}, visibile: {sprite.visible}, dimensione: {sprite.image.width}x{sprite.image.height}, scala: {sprite.scale}, opacità: {sprite.opacity}")
                except pyglet.resource.ResourceNotFoundException:
                    print(f"Errore: immagine {results[i]} non trovata!")
                    sprite.image = pyglet.image.SolidColorImagePattern((255, 0, 0, 255)).create_image(60, 60)
                    sprite.scale = 1.0
                    sprite.position = (436 + (i % 2) * 60, 114 - (i // 2) * 60)
                    sprite.batch = self.batch
            else:
                sprite.visible = False
                sprite.opacity = 0
        print(f"Risultati dadi: {self.dice_results}")
        return self.dice_results

    def get_dice_results(self):
        return self.dice_results

    def on_mouse_release(self, x, y, buttons, modifiers):
        local_x, local_y = x - self.position[0], y - self.position[1]
        if buttons & mouse.LEFT and self.enabled:
            if (self.roll_button.x - 60 <= local_x <= self.roll_button.x + 60 and
                self.roll_button.y - 25 <= local_y <= self.roll_button.y + 25):
                print("Pulsante Tira dadi cliccato!")
                return self.roll_dice()
        return None

# Sistema vittoria
class VictoryLayer(cocos.layer.Layer):
    is_event_handler = True

    def __init__(self, controller):
        super().__init__()
        self.name = 'VictoryLayer'
        self.controller = controller
        self.victory_text = cocos.text.Label(
            "", font_size=30, color=(100, 100, 255, 255), anchor_x='center', anchor_y='center', position=(400, 300)
        )
        self.victory_button = cocos.sprite.Sprite(
            pyglet.image.SolidColorImagePattern((100, 100, 255, 255)).create_image(139, 60), position=(400, 200)
        )
        self.victory_button_label = cocos.text.Label(
            "Torna al menù", font_size=14, color=(255, 255, 255, 255), anchor_x='center', anchor_y='center', position=(400, 200)
        )
        self.add(self.victory_text, z=31)
        self.add(self.victory_button, z=30)
        self.add(self.victory_button_label, z=31)
        banner = cocos.sprite.Sprite("vittoria.png") # img
        banner.position = (400, 80) # img
        self.add(banner) # img
        self.visible = False
        print("Victory layer inizializzato, posizione testo: (400, 300), pulsante: (400, 200), z=100")

    def show_victory(self, winner):
        self.victory_text.element.text = f"Vittoria: {winner.Name}"
        self.visible = True
        self.victory_button.visible = True
        self.victory_button_label.visible = True
        print(f"Victory layer visibile: {self.visible}, testo: {self.victory_text.element.text}")
        
    def on_mouse_release(self, x, y, buttons, modifiers):
        if buttons & mouse.LEFT and self.visible:
            if (self.victory_button.x - 60 <= x <= self.victory_button.x + 60 and
                self.victory_button.y - 25 <= y <= self.victory_button.y + 25):
                from lionheart import MenuLayer, BannerLayer
                banner_layer = BannerLayer()
                menu = MenuLayer("Open Lionheart")
                director.replace(cocos.scene.Scene(banner_layer, menu))
                print("Tornato al menù principale")
                return

# Sistema gioco
class GameView(cocos.layer.Layer):
    is_event_handler = True     
    def __init__(self, controller):
        super().__init__()
        self.name = 'GameView'
        print("Inizializzo GameView")
        self.controller = controller
        self.controller.game_view = self  # Passa il riferimento a GameView
        self.table = TableView(self.controller.tablero)
        self.add(self.table, z=0)
        self.ui_layer = UILayer(is_deploy=False, current_player=self.controller.current_player)
        self.ui_layer.show_end_turn(True)
        self.add(self.ui_layer, z=15)
        self.dice_layer = DiceLayer(self.controller)
        self.add(self.dice_layer, z=20)
        self.victory_layer = VictoryLayer(self.controller)
        self.add(self.victory_layer, z=100)
        self.victory_layer.visible = False
        self.dice_rolled = False
        self.selected_unit = None
        self.target_unit = None
        self._processing_end_turn = False
        self._processing_bot_turn = False
        self.controller.tablero.game_view = self # per funzione panico
        # Verifica unità schierate
        for i in range(self.controller.tablero.rows):
            for j in range(self.controller.tablero.columns):
                self.table.update_cell(i, j)
        if not self.controller.advanced:
            self.dice_layer.set_enabled(True, 2)  # Abilita dadi per modalità base
        print(f"GameView inizializzato: {self.controller.phase}, giocatore: {self.controller.current_player.Name}, celle aggiornate")
        
    def show_victory(self, winner):
        self.victory_layer.show_victory(winner)
        self.is_event_handler = False  # Disabilita input dopo la vittoria
        self.ui_layer.show_end_turn(False)
        self.dice_layer.set_enabled(False)
        print(f"Mostra vittoria: {winner.Name}")
        
    def update_turn(self):
        self.ui_layer.update_text(f"Turno: {self.controller.current_player.Name}")

    def on_mouse_press(self, x, y, buttons, modifiers):
        if self.controller.phase != "gameplay":
            print(f"Ignorato click mouse: fase corrente {self.controller.phase}")
            return

        if self.controller.bot_mode and self.controller.current_player == self.controller.player2:
            print("Ignorato input: turno del bot in corso")
            return

        if buttons & mouse.LEFT:
            # Gestione UI Layer
            ui_action = self.ui_layer.on_mouse_press(x, y, buttons, modifiers)
            if ui_action == "menu":
                try:
                    from lionheart import MenuLayer, BannerLayer
                    banner_layer = BannerLayer()
                    menu = MenuLayer("Open Lionheart")
                    director.replace(cocos.scene.Scene(banner_layer, menu))
                    print("Tornato al menù principale")
                    return
                except Exception as e:
                    print(f"Errore durante la transizione al menù: {e}")
                    return
            # Rimossa la gestione di "end_turn" da on_mouse_press

            # Gestione celle e unità
            cell = self.controller.tablero.get_cell(x, y)
            if cell:
                print(f"Cella cliccata: ({cell.i}, {cell.j})")
                if cell.isUnit and cell.owner == self.controller.current_player and not self.selected_unit:
                    self.select_unit(cell)
                elif self.selected_unit and cell.activated and not cell.isUnit:
                    old_i, old_j = self.selected_unit.i, self.selected_unit.j
                    if self.controller.move_unit(self.selected_unit, cell.i, cell.j):
                        self.table.update_cell(cell.i, cell.j)
                        self.table.update_cell(old_i, old_j)
                        self.selected_unit.deselect()
                        self.selected_unit = None
                        self.controller.tablero.clear_activated()
                        print(f"Unità mossa a ({cell.i}, {cell.j})")
                elif self.selected_unit and cell.isUnit and cell.owner != self.controller.current_player:
                    attack_positions = self.selected_unit.get_attacks(self.controller.tablero)
                    if (cell.i, cell.j) in attack_positions:
                        self.target_unit = cell
                        dice_count = self.selected_unit.get_dice_count(cell)
                        self.dice_layer.set_enabled(True, dice_count)
                        print(f"Obiettivo selezionato: ({cell.i}, {cell.j})")
                    else:
                        self.selected_unit.deselect()
                        self.selected_unit = None
                        self.target_unit = None
                        self.dice_layer.set_enabled(False)
                        self.controller.tablero.clear_activated()
                else:
                    if self.selected_unit:
                        self.selected_unit.deselect()
                        self.selected_unit = None
                    self.target_unit = None
                    self.dice_layer.set_enabled(False)
                    self.controller.tablero.clear_activated()
                    print("Selezione resettata")
        elif buttons & mouse.RIGHT and self.selected_unit:
            self.selected_unit.rotate_orientation()
            self.controller.tablero.clear_activated()
            activated_cells = []
            # Aggiorna celle per il movimento
            for i in range(self.controller.tablero.rows):
                for j in range(self.controller.tablero.columns):
                    if self.controller.tablero.is_valid_move(i, j, self.selected_unit):
                        self.controller.tablero.cell_at(i, j).activate()
                        activated_cells.append((i, j))
            # Aggiorna celle per l'attacco
            attack_positions = self.selected_unit.get_attacks(self.controller.tablero)
            for pos in attack_positions:
                cell = self.controller.tablero.cell_at(pos[0], pos[1])
                if cell and cell.isUnit and cell.owner != self.selected_unit.owner:
                    self.controller.tablero.cell_at(pos[0], pos[1]).activate()
                    activated_cells.append(pos)
            print(f"Rotazione: orientamento {self.selected_unit.orientation}, celle attivate: {activated_cells}")

    def on_mouse_release(self, x, y, buttons, modifiers):
        if self.controller.phase != "gameplay":
            print(f"Ignorato rilascio mouse: fase corrente {self.controller.phase}")
            return

        if self.controller.bot_mode and self.controller.current_player == self.controller.player2:
            print("Ignorato input: turno del bot in corso")
            return

        if self._processing_end_turn or self.controller._processing_bot_turn:
            print("Ignorato input: elaborazione turno in corso")
            return

        if buttons & mouse.LEFT:
            ui_action = self.ui_layer.on_mouse_press(x, y, buttons, modifiers)
            if ui_action == "end_turn":
                if not self._processing_end_turn and not self.controller._processing_bot_turn:
                    self._processing_end_turn = True
                    try:
                        if self.controller.end_turn():
                            self.update_turn()
                            self.dice_layer.set_enabled(False)
                            self.dice_rolled = None
                            self.controller.tablero.clear_activated()
                            if self.selected_unit:
                                self.selected_unit.deselect()
                                self.selected_unit = None
                            self.target_unit = None
                            print(f"Turno terminato, ora tocca a: {self.controller.current_player.Name}")
                    finally:
                        self._processing_end_turn = False
                    return
            dice_results = self.dice_layer.on_mouse_release(x, y, buttons, modifiers)
            if dice_results and self.selected_unit and self.target_unit:
                self.dice_rolled = True
                success, winner = self.controller.perform_attack(self.selected_unit, self.target_unit, dice_results)
                if success:
                    self.table.update_cell(self.target_unit.i, self.target_unit.j)
                    if winner:
                        self.show_victory(winner)
                self.dice_layer.set_enabled(False, hide_dice=False)
                self.selected_unit.deselect()
                self.selected_unit = None
                self.target_unit = None
                self.controller.tablero.clear_activated()
                print("Attacco completato e stato resettato")

    def select_unit(self, unit):
        if unit.action_count >= getattr(unit, 'max_actions', 2):
            print(f"Unità ha esaurito le azioni ({unit.action_count})")
            return
        if self.selected_unit:
            self.selected_unit.deselect()
        self.selected_unit = unit
        self.selected_unit.select()
        self.controller.tablero.clear_activated()
        activated_cells = []
        # Attiva celle per il movimento
        for i in range(self.controller.tablero.rows):
            for j in range(self.controller.tablero.columns):
                if self.controller.tablero.is_valid_move(i, j, self.selected_unit):
                    self.controller.tablero.cell_at(i, j).activate()
                    activated_cells.append((i, j))
        # Attiva celle per l'attacco
        attack_positions = self.selected_unit.get_attacks(self.controller.tablero)
        for pos in attack_positions:
            cell = self.controller.tablero.cell_at(pos[0], pos[1])
            if cell and cell.isUnit and cell.owner != self.selected_unit.owner:
                cell.activate()  # Usa direttamente cell invece di cell_at per maggiore chiarezza
                activated_cells.append(pos)
        print(f"Unità selezionata a ({unit.i}, {unit.j}), celle attivate: {activated_cells}")

    # Dissolvenza per dadi
    def fade_dice(self, dt):
        for sprite in self.dice_layer.dice_sprites:
            sprite.do(cocos.actions.FadeOut(1.5) + cocos.actions.CallFunc(lambda: setattr(sprite, 'visible', False)))
        print("Dadi dissolti dopo 5 secondi")
