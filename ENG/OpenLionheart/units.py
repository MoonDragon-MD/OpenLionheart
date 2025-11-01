# -*- coding: utf-8 -*-
from model import Cell
import cocos
import cocos.sprite
import cocos.text
import pyglet
from cocos.actions import *
from model import Cell, Table

class unit(Cell):
    def __init__(self, image, i, j, x, y, orientation, soldiers, owner, table=None):
        size = 67
        self.soldiers = min(soldiers, 4)  # Limita a max 4 soldati
        x = x if x is not None else 0
        y = y if y is not None else 0
        super().__init__(image, size, i, j, x, y, orientation)
        print(f"Caricamento unità: {image}, proprietario: {owner.Name}, colore: {owner.color}")
        self.isUnit = True
        self.isKing = False
        self.image_loaded = False
        self.hitsPerSoldier = 1
        self.dicePerSoldier = 1
        self.hitsWith = 1
        self.opacity = 255
        self.movements = 1  # Valore predefinito per movimenti
        self.max_actions = 2  # Valore predefinito per max_actions
        self.table = table  # Riferimento a Table per modalità panico
        print(f"Table impostata per {self.__class__.__name__}: {self.table.__class__.__name__ if self.table else 'None'}")
        if soldiers > 9:
            xalign = 13
        else:
            xalign = 20
        self.text = cocos.text.Label(
            "", font_size=12, x=xalign, y=-30, color=(0, 0, 0, 255)
        )
        self.text.element.text = "%d" % (soldiers)
        self.add(self.text, z=3)
        self.owner = owner
        self.color = owner.color[:3]
        print(f"Colore unità impostato: {self.color}")
        print("Caricamento sprite direzione")
        try:
            self.orientation_sprite = cocos.sprite.Sprite("direction.png")
            print("Sprite direzione caricato con successo")
        except pyglet.resource.ResourceNotFoundException:
            print("Errore: 'direction.png' non trovata. Creo sprite vuoto.")
            self.orientation_sprite = cocos.sprite.Sprite(pyglet.image.SolidColorImagePattern((255, 0, 0, 255)).create_image(32, 32))
        self.add(self.orientation_sprite, z=2)
        self.update_orientation()
        self.movementCost = 1
        self.action_count = 0
        self.has_moved = False
        self.has_attacked = False

        try:
            self.selected_border = cocos.sprite.Sprite("select.png")
            self.selected_border.scale = 67 / self.selected_border.image.width
            print("Bordo di selezione caricato con successo")
        except pyglet.resource.ResourceNotFoundException:
            print("Errore: 'select.png' non trovata. Uso placeholder.")
            self.selected_border = cocos.sprite.Sprite(pyglet.image.SolidColorImagePattern((255, 255, 0, 255)).create_image(67, 67))
        self.selected_border.position = (0, 0)
        self.selected_border.visible = False
        self.selected_border.opacity = 255
        self.add(self.selected_border, z=5)  # Higher z-order

        # Primo marker (rettangolo per prima mossa)
        self.move_marker1 = cocos.sprite.Sprite(
            pyglet.image.SolidColorImagePattern((0, 0, 0, 255)).create_image(12, 6)
        )
        self.move_marker1.position = (-25, -25)
        self.move_marker1.visible = False
        self.add(self.move_marker1, z=4)

        # Secondo marker (rettangolo per seconda mossa)
        self.move_marker2 = cocos.sprite.Sprite(
            pyglet.image.SolidColorImagePattern((0, 0, 0, 255)).create_image(12, 6)
        )
        self.move_marker2.position = (-25, -19)
        self.move_marker2.visible = False
        self.add(self.move_marker2, z=4)

        # Salva il riferimento all'immagine originale
        self.original_image = image
        self.load_image()

    def load_image(self):
        if not self.image_loaded:
            print(f"Caricamento immagine: {self.original_image}")
            try:
                img = pyglet.resource.image(self.original_image)
                self.image = img
                self.image.anchor_x = self.image.width // 2
                self.image.anchor_y = self.image.height // 2
                self.opacity = 255
                self.image_loaded = True
                print(f"Immagine caricata: {self.original_image}, dimensioni: {self.image.width}x{self.image.height}, opacità: {self.opacity}")
            except pyglet.resource.ResourceNotFoundException:
                print(f"Errore: {self.original_image} non trovata. Uso placeholder.")
                self.image = pyglet.image.SolidColorImagePattern((255, 0, 0, 255)).create_image(67, 67)
                self.image.anchor_x = self.image.width // 2
                self.image.anchor_y = self.image.height // 2
                self.image_loaded = True

    def update_text(self):
        self.text.element.text = "%d" % (self.soldiers)

    def attack_result(self, diceRoll, defender):
        result = 0
        panic = 0
        for dice in diceRoll:
            if dice == 3:
                panic += 1
            elif self.__class__.__name__ == "peasant":
                result += dice in [1, 2]
            elif self.__class__.__name__ == "crossbowman" and dice == 2:
                result += 2
            else:
                result += dice == self.hitsWith
        print(f"Attacco: {self.__class__.__name__} contro {defender.__class__.__name__}, dadi: {diceRoll}, colpi: {result}, panico: {panic}")
        if panic == len(diceRoll):  # Panico se tutti i dadi
            return [1, 0]  # Panico: nessun colpo
        return [0, result]  # Normale: restituisci i colpi

    def get_attacks(self, tablero):
        unit_type = self.__class__.__name__
        attacks = []
        print(f"Check attacks for {unit_type} a ({self.i}, {self.j}), orientation: {self.orientation}")

        def is_valid_pos(i, j):
            return 0 <= i < 8 and 0 <= j < 9

        def is_enemy_unit(i, j):
            cell = tablero.cell_at(i, j)
            return cell and cell.isUnit and cell.owner != self.owner

        def is_path_clear(start_i, start_j, end_i, end_j):
            if start_i == end_i:
                step = 1 if end_j > start_j else -1
                for j in range(start_j + step, end_j, step):
                    cell = tablero.cell_at(start_i, j)
                    if cell and cell.isUnit:
                        return False
            elif start_j == end_j:
                step = 1 if end_i > start_i else -1
                for i in range(start_i + step, end_i, step):
                    cell = tablero.cell_at(i, start_j)
                    if cell and cell.isUnit:
                        return False
            else:
                return False
            return True

        def is_protected_by_shield_wall(self_i, self_j, target_i, target_j):
            """Verifica se un'unità è protetta da un Muro di scudi contro attacchi a distanza (solo Modo esperto)."""
            # Disattiva la protezione se non in modalità esperto
            if not hasattr(tablero, 'controller') or not tablero.controller or not tablero.controller.expert:
                return False

            target = tablero.cell_at(target_i, target_j)
            if not target or not target.isUnit or target.__class__.__name__ == "shield_wall":
                return False

            for (i, j), unit in tablero.units.items():
                if unit.__class__.__name__ == "shield_wall":
                    if unit.orientation == 1:  # Su
                        if target_i < i and target_j == j:  # Protegge sopra
                            return True
                    elif unit.orientation == 2:  # Destra
                        if target_j > j and target_i == i:  # Protegge a destra
                            return True
                    elif unit.orientation == 3:  # Giù
                        if target_i > i and target_j == j:  # Protegge sotto
                            return True
                    elif unit.orientation == 4:  # Sinistra
                        if target_j < j and target_i == i:  # Protegge a sinistra
                            return True
            return False

        if unit_type == "soldier":
            if self.orientation == 1:  # Su
                pos = (self.i + 1, self.j)
            elif self.orientation == 2:  # Destra
                pos = (self.i, self.j + 1)
            elif self.orientation == 3:  # Giù
                pos = (self.i - 1, self.j)
            elif self.orientation == 4:  # Sinistra
                pos = (self.i, self.j - 1)
            if is_valid_pos(*pos) and is_enemy_unit(*pos):
                attacks.append(pos)

        elif unit_type in ["archer", "crossbowman"]:
            if self.orientation == 1:  # Su
                candidates = [
                    (self.i + 1, self.j - 1), (self.i + 1, self.j), (self.i + 1, self.j + 1),
                    (self.i + 2, self.j - 1), (self.i + 2, self.j), (self.i + 2, self.j + 1),
                    (self.i + 3, self.j - 1), (self.i + 3, self.j), (self.i + 3, self.j + 1),
                ]
            elif self.orientation == 2:  # Destra
                candidates = [
                    (self.i - 1, self.j + 1), (self.i, self.j + 1), (self.i + 1, self.j + 1),
                    (self.i - 1, self.j + 2), (self.i, self.j + 2), (self.i + 1, self.j + 2),
                    (self.i - 1, self.j + 3), (self.i, self.j + 3), (self.i + 1, self.j + 3),
                ]
            elif self.orientation == 3:  # Giù
                candidates = [
                    (self.i - 1, self.j - 1), (self.i - 1, self.j), (self.i - 1, self.j + 1),
                    (self.i - 2, self.j - 1), (self.i - 2, self.j), (self.i - 2, self.j + 1),
                    (self.i - 3, self.j - 1), (self.i - 3, self.j), (self.i - 3, self.j + 1),
                ]
            elif self.orientation == 4:  # Sinistra
                candidates = [
                    (self.i - 1, self.j - 1), (self.i, self.j - 1), (self.i + 1, self.j - 1),
                    (self.i - 1, self.j - 2), (self.i, self.j - 2), (self.i + 1, self.j - 2),
                    (self.i - 1, self.j - 3), (self.i, self.j - 3), (self.i + 1, self.j - 3),
                ]
            for pos in candidates:
                if is_valid_pos(*pos) and is_enemy_unit(*pos) and not is_protected_by_shield_wall(self.i, self.j, *pos):
                    attacks.append(pos)
                    print(f"{unit_type} a ({self.i}, {self.j}), orientamento {self.orientation}: attacco valido a {pos}")
                else:
                    print(f"{unit_type} a ({self.i}, {self.j}), orientamento {self.orientation}: attacco non valido a {pos} (valido={is_valid_pos(*pos)}, nemico={is_enemy_unit(*pos)}, protetto={is_protected_by_shield_wall(self.i, self.j, *pos)})")
        elif unit_type in ["knight", "king", "peasant"]:
            if self.orientation == 1:  # Su
                pos = (self.i + 1, self.j)
            elif self.orientation == 2:  # Destra
                pos = (self.i, self.j + 1)
            elif self.orientation == 3:  # Giù
                pos = (self.i - 1, self.j)
            elif self.orientation == 4:  # Sinistra
                pos = (self.i, self.j - 1)
            if is_valid_pos(*pos) and is_enemy_unit(*pos):
                attacks.append(pos)

        elif unit_type in ["heavy_infantry", "mercenary"]:
            candidates = [
                (self.i + 1, self.j - 1), (self.i + 1, self.j), (self.i + 1, self.j + 1),
                (self.i, self.j - 1), (self.i, self.j + 1),
                (self.i - 1, self.j - 1), (self.i - 1, self.j), (self.i - 1, self.j + 1),
            ]
            for pos in candidates:
                if is_valid_pos(*pos) and is_enemy_unit(*pos):
                    attacks.append(pos)

        return attacks

    def kill(self, impacts):
        if impacts < 0:
            print(f"Errore: impacts negativo ({impacts}), impostato a 0")
            impacts = 0
        damage = round(impacts / self.hitsPerSoldier)
        print(f"Unità {self.__class__.__name__} a ({self.i}, {self.j}): impatti={impacts}, hitsPerSoldier={self.hitsPerSoldier}, danni={damage}, soldati prima={self.soldiers}")
        self.soldiers -= damage
        print(f"Unità {self.__class__.__name__} a ({self.i}, {self.j}): soldati dopo={self.soldiers}")
        self.update_text()
        if self.soldiers <= 0:
            print(f"Unità {self.__class__.__name__} distrutta")
            return True  # Consenti al re di essere distrutto
        return False

    def panic(self, table, panicked_units=None):
        if self.isKing or self.__class__.__name__ == "mercenary":
            print(f"Unità {self.__class__.__name__} immune al panico")
            return False

        if panicked_units is None:
            panicked_units = set()

        if (self.i, self.j) in panicked_units:
            print(f"Unità {self.__class__.__name__} a ({self.i}, {self.j}) già in panico, interrompo")
            return False

        panicked_units.add((self.i, self.j))

        print(f"Unità {self.__class__.__name__} a ({self.i}, {self.j}) tenta di entrare in panico")
        if self.soldiers <= 0:
            print("Unità già distrutta, nessun movimento di panico")
            return False

        if self.orientation == 1:
            target_i, target_j = self.i - 1, self.j
        elif self.orientation == 2:
            target_i, target_j = self.i, self.j - 1
        elif self.orientation == 3:
            target_i, target_j = self.i + 1, self.j
        elif self.orientation == 4:
            target_i, target_j = self.i, self.j + 1
        else:
            print(f"Orientamento non valido: {self.orientation}")
            return False

        print(f"Table associata: {table.__class__.__name__ if table else 'None'}")
        if not isinstance(table, Table):
            print("Errore: table non è un'istanza di Table")
            return False

        if not (0 <= target_i < table.rows and 0 <= target_j < table.columns):
            print(f"Unità {self.__class__.__name__} esce dalla griglia a ({target_i}, {target_j}), eliminata")
            if (self.i, self.j) in table.units:
                table.units.pop((self.i, self.j))
            self.owner.units.remove(self)
            table.insert_cell(self.i, self.j, None)
            self.destroy()
            if hasattr(table, 'game_view'):
                table.game_view.table.update_cell(self.i, self.j)
            return True

        target_cell = table.cell_at(target_i, target_j)
        if target_cell and target_cell.isUnit:
            if target_cell.owner == self.owner:
                print(f"Collisione con unità alleata a ({target_i}, {target_j}), propago panico")
                propagated = target_cell.panic(table, panicked_units)
                if propagated:
                    print(f"Panico propagato, verifico nuovamente la cella ({target_i}, {target_j})")
                    target_cell = table.cell_at(target_i, target_j)
                    if not target_cell or not target_cell.isUnit:
                        old_i, old_j = self.i, self.j
                        if table.deploy_unit(target_i, target_j, self):
                            table.insert_cell(old_i, old_j, None)
                            print(f"Unità {self.__class__.__name__} spostata in panico da ({old_i}, {old_j}) a ({target_i}, {target_j})")
                            if hasattr(table, 'game_view'):
                                table.game_view.table.update_cell(target_i, target_j)
                                table.game_view.table.update_cell(old_i, old_j)
                            return True
            else:
                print(f"Cella occupata da nemico a ({target_i}, {target_j}), non posso muovere")
                return False
        else:
            old_i, old_j = self.i, self.j
            if table.deploy_unit(target_i, target_j, self):
                table.insert_cell(old_i, old_j, None)
                print(f"Unità {self.__class__.__name__} spostata in panico da ({old_i}, {old_j}) a ({target_i}, {target_j})")
                if hasattr(table, 'game_view'):
                    table.game_view.table.update_cell(target_i, target_j)
                    table.game_view.table.update_cell(old_i, old_j)
                return True
            else:
                print(f"Errore nello spostamento di panico a ({target_i}, {target_j})")
                return False

    def update_orientation(self):
        # Degree orientation map (assuming direction.png points up)
        angle_map = {
            1: 0,    # Up
            2: 90,   # Right
            3: 180,  # Down
            4: 270   # Left
        }
        # Reset the current rotation to avoid build-up
        self.orientation_sprite.rotation = 0
        # Apply the new angle
        self.orientation_sprite.rotation = angle_map.get(self.orientation, 0)
        print(f"Updated orientation: {self.orientation}, angle: {self.orientation_sprite.rotation}")

    def rotate_orientation(self):
        self.orientation = (self.orientation % 4) + 1
        self.update_orientation()
        print(f"Rotation: orientation {self.orientation}, angle sprite: {self.orientation_sprite.rotation}")
        return True

    def move(self):
        max_actions = getattr(self, 'max_actions', 2)
        if self.action_count < max_actions:
            self.action_count += 1
            self.has_moved = True
            if self.action_count == 1:
                self.move_marker1.visible = True
            elif self.action_count == 2:
                self.move_marker2.visible = True
            # Per unità con max_actions = 1, mostra entrambi i marcatori immediatamente
            if max_actions == 1:
                self.move_marker1.visible = True
                self.move_marker2.visible = True
                self.action_count = 2  # Simula l'esaurimento delle azioni
            print(f"Movimento: {self.__class__.__name__} a ({self.i}, {self.j}), action_count={self.action_count}/{max_actions}, marker1={self.move_marker1.visible}, marker2={self.move_marker2.visible}")
            return True
        print(f"Movimento non valido: action_count={self.action_count}/{max_actions}")
        return False

    def attack(self):
        max_actions = getattr(self, 'max_actions', 2)
        if self.action_count < max_actions and not self.has_attacked:
            self.action_count += 1
            self.has_attacked = True
            # Aggiorna i marcatori in base ad action_count
            if self.action_count >= 1:
                self.move_marker1.visible = True
            if self.action_count >= 2:
                self.move_marker2.visible = True
            # Per unità con max_actions = 1, forza entrambi i marcatori
            if max_actions == 1:
                self.move_marker1.visible = True
                self.move_marker2.visible = True
                self.action_count = 2  # Esaurisci le azioni
            print(f"Attacco: {self.__class__.__name__} a ({self.i}, {self.j}), has_attacked={self.has_attacked}, action_count={self.action_count}/{max_actions}, marker1={self.move_marker1.visible}, marker2={self.move_marker2.visible}")
            # Forza l'aggiornamento della posizione per garantire la visibilità
            self.update_position()
            return True
        print(f"Attacco non valido: {self.__class__.__name__} a ({self.i}, {self.j}), has_attacked={self.has_attacked}, action_count={self.action_count}/{max_actions}")
        return False
    
    def get_dice_count(self, defender):
        dice_count = min(self.dicePerSoldier * self.soldiers, 4)
        if defender.__class__.__name__ in ["king", "knight", "heavy_infantry"]:
            if defender.soldiers == 1 and self.soldiers == 1:
                dice_count = max(dice_count, 2)
                print(f"Dadi aumentati a {dice_count} per attacco di {self.__class__.__name__} (1 soldato) contro {defender.__class__.__name__} (1 soldato)")
        return dice_count

    def update_position(self):
        self.position = (self.posx, self.posy)
        self.visible = True
        self.opacity = 255
        self.text.position = (self.text.x, self.text.y)
        self.orientation_sprite.position = (0, 0)
        self.selected_border.position = (0, 0)
        self.move_marker1.position = (-25, -25)
        self.move_marker2.position = (-25, -19)
        self.text.visible = True
        self.text.opacity = 255
        self.orientation_sprite.visible = True
        self.orientation_sprite.opacity = 255
        self.selected_border.visible = self.selected_border.visible
        self.selected_border.opacity = 255 if self.selected_border.visible else 0
        self.move_marker1.visible = self.move_marker1.visible
        self.move_marker1.opacity = 255 if self.move_marker1.visible else 0
        self.move_marker2.visible = self.move_marker2.visible
        self.move_marker2.opacity = 255 if self.move_marker2.visible else 0
        print(f"Posizione aggiornata: ({self.posx}, {self.posy}), visibile: {self.visible}, opacità: {self.opacity}, marker1_visible={self.move_marker1.visible}, marker2_visible={self.move_marker2.visible}")
		
    def setOrientation(self, o):
        # Degree orientation map
        angle_map = {
            1: 0,    # Up
            2: 90,   # Right
            3: 180,  # Down
            4: 270   # Left
        }
        self.orientation = o
        self.orientation_sprite.rotation = 0  # Reset
        self.orientation_sprite.rotation = angle_map.get(self.orientation, 0)
        print(f"Set orientation: {self.orientation}, angle: {self.orientation_sprite.rotation}")

    def activate(self):
        self.color = (255, 154, 50)
        self.activated = True

    def deactivate(self):
        self.color = self.owner.color[:3]
        self.activated = False

    def select(self):
        self.selected_border.visible = True
        self.selected_border.opacity = 255
        print(f"Unità selezionata: bordo visibile, opacità={self.selected_border.opacity}")
        
    def deselect(self):
        self.selected_border.visible = False
        print(f"Deselezionata unità: {self.__class__.__name__} a ({self.i}, {self.j}), action_count={self.action_count}/{self.max_actions}, marker1={self.move_marker1.visible}, marker2={self.move_marker2.visible}, bordo_nascosto=True")

    def reset_action(self):
        self.action_count = 0
        self.has_moved = False
        self.has_attacked = False
        self.move_marker1.visible = False
        self.move_marker2.visible = False
        self.image_loaded = False
        self.load_image()
        print(f"Azioni resettate: {self.__class__.__name__} a ({self.i}, {self.j})")
        
    # Per togliere visivamente unità uccise 
    def destroy(self):
        if self.parent:
            self.parent.remove(self)
            print(f"Unità {self.__class__.__name__} rimossa dalla scena")
        
# Classi derivate
class soldier(unit):
    def __init__(self, i, j, x, y, orientation, soldiers, owner, table=None):
        super().__init__("soldado.png", i, j, x, y, orientation, soldiers, owner)
        self.movements = 1

class archer(unit):
    def __init__(self, i, j, x, y, orientation, soldiers, owner, table=None):
        super().__init__("archer.png", i, j, x, y, orientation, soldiers, owner)
        self.movements = 1
        self.hitsWith = 2
        self.max_actions = 2 

class knight(unit):
    def __init__(self, i, j, x, y, orientation, soldiers, owner, table=None):
        super().__init__("knight.png", i, j, x, y, orientation, soldiers, owner)
        self.movements = 2
        self.hitsPerSoldier = 2
        self.dicePerSoldier = 2

class king(unit):
    def __init__(self, i, j, x, y, orientation, owner, table=None):
        super().__init__("king.png", i, j, x, y, orientation, 1, owner)
        self.movements = 8
        self.isKing = True
        self.hitsPerSoldier = 2
        self.dicePerSoldier = 2

class peasant(unit):
    def __init__(self, i, j, x, y, orientation, soldiers, owner, table=None):
        super().__init__("peasant.png", i, j, x, y, orientation, soldiers, owner)
        self.movements = 1

class heavy_infantry(unit):
    def __init__(self, i, j, x, y, orientation, soldiers, owner, table=None):
        super().__init__("heavy_infantry.png", i, j, x, y, orientation, soldiers, owner)
        self.movements = 1
        self.hitsPerSoldier = 2
        self.dicePerSoldier = 2
        self.movementCost = 1
        self.max_actions = 1  # Limit to 1 action per turn

class mercenary(unit):
    def __init__(self, i, j, x, y, orientation, soldiers, owner, table=None):
        super().__init__("mercenary.png", i, j, x, y, orientation, soldiers, owner)
        self.movements = 1
        self.hitsPerSoldier = 2
        self.dicePerSoldier = 2
        
class crossbowman(unit):
    def __init__(self, i, j, x, y, orientation, soldiers, owner, table=None):
        super().__init__("crossbowman.png", i, j, x, y, orientation, soldiers, owner, table)
        self.movements = 1
        self.hitsWith = 2  # Colpisce con freccia
        self.hitsPerSoldier = 1
        self.dicePerSoldier = 1
        self.max_actions = 1  # Esplicito per evitare problemi

    def reset_action(self):
        self.action_count = 0
        self.has_moved = False
        self.has_attacked = False
        self.move_marker1.visible = False
        self.move_marker2.visible = False
        self.image_loaded = False
        self.load_image()
        print(f"Azioni resettate: {self.__class__.__name__} a ({self.i}, {self.j}), marker1={self.move_marker1.visible}, marker2={self.move_marker2.visible}")
		
class shield_wall(unit):
    def __init__(self, i, j, x, y, orientation, soldiers, owner, table=None):
        super().__init__("shield_wall.png", i, j, x, y, orientation, soldiers, owner, table)
        self.movements = 1
        self.hitsPerSoldier = 1
        self.dicePerSoldier = 0  # Non attacca
        self.max_actions = 2  # Movimento
