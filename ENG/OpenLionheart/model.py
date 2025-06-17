# -*- coding: utf-8 -*-
import cocos
from cocos.actions import *
import cocos.tiles
from cocos.director import director
import pyglet
import copy

class Player(object):
    def __init__(self, num_player, color, name, units):
        super().__init__()
        self.player = num_player
        self.color = color
        self.Name = name
        self.units = units

class Table(cocos.layer.Layer):
    def __init__(self, rows, columns, cell_size, cell_image, controller=None):
        super().__init__()
        self.controller = controller  # Riferimento al GameController
        self.cell_list = []
        self.units = {}  # Dizionario per tracciare unità: (i, j) -> unit
        self.cell_size = cell_size
        self.rows = rows
        self.columns = columns
        i = 0
        j = 0
        while i < rows:
            row_list = []
            while j < columns:
                cell = Cell(cell_image, cell_size, i, j, round(cell_size/2)+1+cell_size*j, round(cell_size/2)+1+cell_size*i, 0)
                row_list.append(cell)
                j += 1
            self.cell_list.append(row_list)
            j = 0
            i += 1
        print("Tavolo inizializzato")

    def print_cells(self):
        for row in self.cell_list:
            for cell in row:
                self.add(cell, z=0)

    def deploy_unit(self, i, j, unit):
        if 0 <= i < self.rows and 0 <= j < self.columns:
            unit.i = i
            unit.j = j
            unit.posx = self.cell_list[i][j].posx
            unit.posy = self.cell_list[i][j].posy
            print(f"Schieramento unità {unit.__class__.__name__} a ({i}, {j}), posizione: ({unit.posx}, {unit.posy})")
            if (i, j) in self.units:
                old_unit = self.units[(i, j)]
                if old_unit != unit:
                    self.remove(old_unit)
                    print(f"Rimossa unità esistente {old_unit.__class__.__name__} a ({i}, {j})")
            self.units[(i, j)] = unit
            if unit.parent != self:
                if unit.parent:
                    unit.parent.remove(unit)
                    print(f"Rimosso parent precedente: {unit.parent.__class__.__name__ if unit.parent else 'None'}")
                self.add(unit, z=1)
                print(f"Aggiunto unità a Table, parent attuale: {unit.parent.__class__.__name__}")
            unit.update_position()
            return True
        print(f"Schieramento fallito: coordinate non valide ({i}, {j})")
        return False

    def get_cell(self, x, y):
        cell_size = self.cell_size  # 67
        offset_x = 100
        offset_y = 186
        grid_j = int((x - offset_x) // cell_size)
        grid_i = int((y - offset_y) // cell_size)
        if 0 <= grid_i < self.rows and 0 <= grid_j < self.columns:
            cell = self.cell_at(grid_i, grid_j)
            if cell:
                return cell
        return None

    def get(self, j):
        if not hasattr(self, '_cell_positions'):
            self._cell_positions = {}
        if j not in self._cell_positions:
            self._cell_positions[j] = round(self.cell_size/2) + 1 + self.cell_size * j
        return self._cell_positions[j]

    def cell_at(self, i, j):
        if 0 <= i < self.rows and 0 <= j < self.columns:
            return self.units.get((i, j), self.cell_list[i][j])
        return None

    def insert_cell(self, i, j, new_cell):
        if 0 <= i < self.rows and 0 <= j < self.columns:
            if (i, j) in self.units:
                unit = self.units.pop((i, j))
                # Non tentare di rimuovere l'unità dal genitore qui
                print(f"Unità {unit.__class__.__name__} rimossa da ({i}, {j})")
            if new_cell:
                self.units[(i, j)] = new_cell
                self.add(new_cell, z=1)
        else:
            print(f"Inserimento cella fallito: coordinate non valide ({i}, {j})")

    def clear_activated(self):
        for row in self.cell_list:
            for cell in row:
                if cell.activated:
                    cell.deactivate()
        for unit in self.units.values():
            if unit.activated:
                unit.deactivate()

    def is_valid_move(self, row, col, unit):
        if not (0 <= row < self.rows and 0 <= col < self.columns):
            print(f"Movimento non valido: coordinate ({row}, {col}) fuori griglia")
            return False
        if (row, col) in self.units:
            print(f"Movimento non valido: cella ({row}, {col}) occupata da {self.units[(row, col)].__class__.__name__}")
            return False
        if unit.action_count >= getattr(unit, 'max_actions', 2):
            print(f"Movimento non valido: unità ha effettuato {unit.action_count} azioni")
            return False
        current_row, current_col = unit.i, unit.j
        distance = abs(row - current_row) + abs(col - current_col)
        if unit.__class__.__name__ in ["king", "knight"]:
            if row != current_row and col != current_col:
                print(f"Movimento non valido: re/cavaliere devono muoversi in linea retta")
                return False
            if row == current_row:
                dj = 1 if col > current_col else -1
                for step in range(1, abs(col - current_col) + 1):
                    check_col = current_col + dj * step
                    if (row, check_col) in self.units:
                        print(f"Movimento non valido: ostacolo a ({row}, {check_col})")
                        return False
            elif col == current_col:
                di = 1 if row > current_row else -1
                for step in range(1, abs(row - current_row) + 1):
                    check_row = current_row + di * step
                    if (check_row, col) in self.units:
                        print(f"Movimento non valido: ostacolo a ({check_row}, {col})")
                        return False
            if distance > unit.movements:
                print(f"Movimento non valido: distanza {distance} > movimenti {unit.movements}")
                return False
            print(f"Movimento valido per {unit.__class__.__name__}: da ({current_row}, {current_col}) a ({row}, {col}), distanza: {distance}, movimenti: {unit.movements}")
            return True
        else:
            if distance > unit.movements:
                print(f"Movimento non valido: distanza {distance} > movimenti {unit.movements}")
                return False
            print(f"Movimento valido per {unit.__class__.__name__}: da ({current_row}, {current_col}) a ({row}, {col}), distanza: {distance}, movimenti: {unit.movements}")
            return True

class Cell(cocos.sprite.Sprite):
    def __init__(self, image, size, i, j, x, y, orientation):
        super().__init__(image, position=(x, y))
        self.size = size
        self.orientation = orientation
        self.posx = x
        self.posy = y
        self.i = i
        self.j = j
        self.activated = False
        self.isUnit = False

    def inrange(self, x, y):
        if ((x < self.posx + self.size/2 and x > self.posx - self.size/2) and
                (y < self.posy + self.size/2 and y > self.posy - self.size/2)):
            return True
        return False

    def update_position(self):
        self.position = (self.posx, self.posy)

    def activate(self):
        self.color = (154, 205, 50)
        self.activated = True

    def deactivate(self):
        self.color = (255, 255, 255)
        self.activated = False
