# -*- coding: utf-8 -*-
from model import *
import pyglet
from pyglet import image
from cocos import *
from cocos.director import director
import random
from pyglet import clock

class GameController(object):
    def __init__(self, advanced=False, bot_mode=False, expert=False, game_view=None):
        self.advancedGame = advanced
        self.expert = expert # Variabile per modo esperto
        self.tablero = Table(8, 9, 67, "cuadrado.png", controller=self)  # Passa il controller
        self.tablero.position = (0, 186)
        self.player1 = Player(1, (0, 255, 255, 255), "Player 1", [])
        self.player2 = Player(2, (255, 165, 0, 255), "Bot" if bot_mode else "Player 2", [])
        self.current_player = self.player1
        self.advanced = advanced # Variabile per modo avanzato
        self.bot_mode = bot_mode
        self.phase = "deployment"
        self._bot_turn_scheduled = False
        self._processing_bot_turn = False
        self.game_view = game_view # Aggiungi riferimento a GameView
        print("GameController initialized, expert=", self.expert)

    def end_turn(self):
        if self.phase != "gameplay":
            print(f"Fase non valida per fine turno: {self.phase}")
            return False

        if self._processing_bot_turn:
            print("Ignorato end_turn: elaborazione turno bot in corso")
            return False

        if hasattr(self, '_end_turn_in_progress') and self._end_turn_in_progress:
            print("Ignorato end_turn: chiamata ridondante")
            return False

        self._end_turn_in_progress = True
        print(f"Terminando turno per {self.current_player.Name}")
        try:
            # Log delle unità prima del reset
            print(f"Unità in tablero.units prima del reset: {[(u.i, u.j, u.__class__.__name__, u.owner.Name) for u in self.tablero.units.values() if u.isUnit]}")
            for unit in self.tablero.units.values():
                if unit.isUnit and unit.owner == self.current_player:
                    print(f"Resettando azioni per {unit.__class__.__name__} a ({unit.i}, {unit.j}), proprietario: {unit.owner.Name}")
                    unit.reset_action()
            # Log delle unità dopo il reset
            print(f"Unità in tablero.units dopo il reset: {[(u.i, u.j, u.__class__.__name__, u.owner.Name, u.action_count) for u in self.tablero.units.values() if u.isUnit]}")
        finally:
            self._end_turn_in_progress = False
            print(f"Fine turno completata, ora tocca a: {self.current_player.Name}")

        previous_player = self.current_player
        self.current_player = self.player2 if self.current_player == self.player1 else self.player1
        print(f"Turno passato da {previous_player.Name} a {self.current_player.Name}")

        if hasattr(self, 'game_view') and self.game_view:
            self.game_view.update_turn()
            print(f"Interfaccia utente aggiornata: Turno di {self.current_player.Name}")

        if self.bot_mode and self.current_player == self.player2 and not self._bot_turn_scheduled:
            print(f"Bot mode: {self.bot_mode}, Current player: {self.current_player.Name}")
            self._bot_turn_scheduled = True
            self._processing_bot_turn = True
            pyglet.clock.schedule_once(self.execute_bot_turn, 2.0)
            print("Turno bot programmato")

        return True

    def execute_bot_turn(self, dt):
        if not self._processing_bot_turn:
            print("Ignorato execute_bot_turn: nessuna elaborazione bot in corso")
            return
        try:
            self.bot_turn()
        finally:
            self._processing_bot_turn = False
            self._bot_turn_scheduled = False
            pyglet.clock.schedule_once(self.finish_bot_turn, 0.5)

    def finish_bot_turn(self, dt):
        if self.current_player == self.player2:
            print("Completamento turno bot")
            self.end_turn()
        
    def next_phase(self):
        """ Gestisce il passaggio alla fase successiva """
        if self.phase == "deployment":
            print("Transizione a fase gameplay")
            self.phase = "gameplay"
        elif self.phase == "gameplay":
            self.phase = "endgame"
            print("Fine del gioco")

    def initialize_table(self):
        self.tablero = Table(8, 9, 67, "cuadrado.png", controller=self)  # Passa il controller
        self.tablero.position = (0, 186)
        self.player1.units = []
        self.player2.units = []
        print("Table reinitialized in GameController")

    def end_deployment(self):
        self.phase = "gameplay"  # Aggiorna phase
        print(f"Fase di gioco aggiornata a: {self.phase}")
    
    def schedule_bot_turn(self):
        if not self._processing_bot_turn:
            print("Ignorato schedule_bot_turn: nessuna elaborazione bot in corso")
            return
        print("Programmazione turno del bot")
        pyglet.clock.schedule_once(self.execute_bot_turn, 2.5)  # Aumentato il delay
        print("Turno bot programmato con ritardo di 2 sec. e mezzo")

    def move_unit(self, unit, i, j):
        if self.phase != "gameplay":
            print(f"Operazione non valida nella fase {self.phase}")
            return False
        if self.tablero.is_valid_move(i, j, unit) and unit.move():
            old_i, old_j = unit.i, unit.j
            if self.tablero.deploy_unit(i, j, unit):
                self.tablero.units.pop((old_i, old_j), None)
                print(f"Unità {unit.__class__.__name__} mossa da ({old_i}, {old_j}) a ({i}, {j}), posizione: ({unit.posx}, {unit.posy})")
                # Aggiorna la visualizzazione
                if hasattr(self, 'game_view'):
                    self.game_view.table.update_cell(i, j)
                    self.game_view.table.update_cell(old_i, old_j)
                return True
            else:
                print(f"Errore in deploy_unit a ({i}, {j})")
                return False
        print(f"Movimento non valido: coordinate ({i}, {j}), action_count: {unit.action_count}, has_moved: {unit.has_moved}")
        return False

    def perform_attack(self, attacker, target, dice_results):
        print(f"Eseguo attacco da {attacker.__class__.__name__} ({attacker.owner.Name}) "
              f"a {target.__class__.__name__} ({target.owner.Name}) con dadi {dice_results}")

        if not attacker or not target or attacker.owner == target.owner:
            print("Attacco non valido: unità non valide o stesso proprietario")
            return False, None

        if attacker.action_count >= getattr(attacker, 'max_actions', 2):
            print(f"Attacco non valido: unità ha esaurito le azioni ({attacker.action_count})")
            return False, None

        attack_positions = attacker.get_attacks(self.tablero)
        target_pos = (target.i, target.j)
        if not target_pos or target_pos not in attack_positions:
            print(f"Attacco non valido: bersaglio a {target_pos} non in {attack_positions}")
            return False, None

        if not attacker.attack():
            print("Attacco non valido: impossibile eseguire attack()")
            return False, None

        panic, hits = attacker.attack_result(dice_results, target)
        print(f"Risultato attacco: panico={panic}, colpi={hits}")

        if panic:
            if attacker.panic(self.tablero, set()):
                print(f"Attaccante {attacker.__class__.__name__} a ({attacker.i}, {attacker.j}) è andato in panico")
                if (attacker.i, attacker.j) in self.tablero.units:
                    self.tablero.units.pop((attacker.i, attacker.j))
                self.tablero.insert_cell(attacker.i, attacker.j, None)
                if attacker in attacker.owner.units:
                    attacker.owner.units.remove(attacker)
                if attacker.isKing:
                    print(f"Re di {attacker.owner.Name} distrutto, vittoria di {target.owner.Name}")
                    return True, target.owner
                return True, None

        if hits > 0:
            destroyed = target.kill(hits)
            if destroyed:
                print(f"Bersaglio {target.__class__.__name__} a {target_pos} distrutto")
                self.tablero.units.pop(target_pos)
                self.tablero.insert_cell(target_pos[0], target_pos[1], None)
                if target in target.owner.units:
                    target.owner.units.remove(target)
                target.destroy()
                if target.isKing:
                    print(f"Re di {target.owner.Name} distrutto, vittoria di {attacker.owner.Name}")
                    return True, attacker.owner

        return True, None
    
    def find_closest_valid_move(self, current_i, current_j, target_i, target_j, movements):
        print(f"Bot: Cerco mossa valida da ({current_i}, {current_j}) verso ({target_i}, {target_j}) con {movements} movimenti")
        valid_moves = []
        unit = self.tablero.units.get((current_i, current_j))
        rows, cols = 8, 9

        if unit.__class__.__name__ in ['king', 'knight']:
            directions = [(0, 1), (0, -1), (1, 0), (-1, 0)]
            for di, dj in directions:
                for dist in range(1, movements + 1):
                    new_i = current_i + di * dist
                    new_j = current_j + dj * dist
                    if 0 <= new_i < rows and 0 <= new_j < cols:
                        if self.tablero.is_valid_move(new_i, new_j, unit):
                            valid_moves.append((new_i, new_j))
                            print(f"Bot: Mossa valida trovata: ({new_i}, {new_j})")
                        else:
                            print(f"Bot: Mossa non valida a ({new_i}, {new_j})")
                    else:
                        print(f"Bot: Fuori griglia: ({new_i}, {new_j})")
                        break
        else:
            for di in range(-movements, movements + 1):
                for dj in range(-movements, movements + 1):
                    new_i = current_i + di
                    new_j = current_j + dj
                    distance = abs(di) + abs(dj)
                    if 0 <= new_i < rows and 0 <= new_j < cols and distance <= movements and distance > 0:
                        if self.tablero.is_valid_move(new_i, new_j, unit):
                            valid_moves.append((new_i, new_j))
                            print(f"Bot: Mossa valida trovata: ({new_i}, {new_j})")
                        else:
                            print(f"Bot: Mossa non valida a ({new_i}, {new_j})")

        if not valid_moves:
            print(f"Bot: Nessuna mossa valida trovata")
            return None, None

        best_move = min(valid_moves, key=lambda pos: abs(pos[0] - target_i) + abs(pos[1] - target_j))
        print(f"Bot: Migliore mossa trovata: ({best_move[0]}, {best_move[1]})")
        return best_move[0], best_move[1]
            
    def bot_turn(self):
        print("Bot: Inizio turno")
        # Resetta stato
        self.tablero.clear_activated()
        if hasattr(self, 'game_view') and self.game_view.selected_unit:
            self.game_view.selected_unit.deselect()
            self.game_view.selected_unit = None
        enemy_units = [(i, j) for (i, j), unit in self.tablero.units.items() if unit.owner == self.player1]
        print(f"Bot: Nemici trovati: {enemy_units}")
        if not enemy_units:
            print("Bot: Nessun nemico rimasto")
            if hasattr(self, 'game_view'):
                self.game_view.show_victory(self.player2)
            return

        def get_best_orientation(unit_pos, target_pos):
            di = target_pos[0] - unit_pos[0]
            dj = target_pos[1] - unit_pos[1]
            if abs(di) > abs(dj):
                return 1 if di < 0 else 3  # 1 = su, 3 = giù
            else:
                return 4 if dj < 0 else 2  # 4 = sinistra, 2 = destra

        if self.expert:
            # Fase 0: Proteggi Arcieri e Balestrieri con Muri di scudi
            ranged_units = [(i, j, unit) for (i, j), unit in self.tablero.units.items() 
                            if unit.owner == self.player2 and unit.__class__.__name__ in ["archer", "crossbowman"]]
            shield_walls = [(i, j, unit) for (i, j), unit in self.tablero.units.items() 
                            if unit.owner == self.player2 and unit.__class__.__name__ == "shield_wall"]
            print(f"Bot: Unità a distanza: {[(i, j, u.__class__.__name__) for i, j, u in ranged_units]}")
            print(f"Bot: Muri di scudi: {[(i, j, u.__class__.__name__) for i, j, u in shield_walls]}")

            for ri, rj, ranged_unit in ranged_units:
                if ranged_unit.action_count >= ranged_unit.max_actions:
                    print(f"Bot: {ranged_unit.__class__.__name__} a ({ri}, {rj}) ha esaurito azioni")
                    continue
                # Cerca un Muro di scudi da posizionare davanti (verso il basso, riga inferiore)
                target_i = ri - 1  # Riga davanti (es. 6 se Arciere in 7)
                target_j = rj      # Stessa colonna
                if not (0 <= target_i < 8 and 0 <= target_j < 9):
                    print(f"Bot: Posizione di protezione ({target_i}, {target_j}) fuori griglia")
                    continue
                if self.tablero.cell_at(target_i, target_j) and self.tablero.cell_at(target_i, target_j).isUnit:
                    print(f"Bot: Posizione di protezione ({target_i}, {target_j}) occupata")
                    continue
                # Trova il Muro di scudi più vicino
                closest_shield = min(shield_walls, 
                                     key=lambda sw: abs(sw[0] - target_i) + abs(sw[1] - target_j),
                                     default=None)
                if closest_shield:
                    si, sj, shield_unit = closest_shield
                    if shield_unit.action_count >= shield_unit.max_actions:
                        print(f"Bot: Muro di scudi a ({si}, {sj}) ha esaurito azioni")
                        continue
                    # Muovi il Muro di scudi verso la posizione di protezione
                    new_i, new_j = self.find_closest_valid_move(si, sj, target_i, target_j, shield_unit.movements)
                    if new_i is not None and new_j is not None:
                        if self.move_unit(shield_unit, new_i, new_j):
                            shield_unit.setOrientation(3)  # Orientamento verso il basso
                            print(f"Bot: Muro di scudi a ({si}, {sj}) mosso a ({new_i}, {new_j}) per proteggere {ranged_unit.__class__.__name__}")
                            # Aggiorna la posizione del Muro
                            shield_walls = [(new_i, new_j, shield_unit) if s == closest_shield else s for s in shield_walls]
                            # Se possibile, muovi di nuovo
                            if shield_unit.action_count < shield_unit.max_actions:
                                new_i2, new_j2 = self.find_closest_valid_move(new_i, new_j, target_i, target_j, shield_unit.movements)
                                if new_i2 is not None and new_j2 is not None and (new_i2, new_j2) != (new_i, new_j):
                                    if self.move_unit(shield_unit, new_i2, new_j2):
                                        shield_unit.setOrientation(3)
                                        print(f"Bot: Muro di scudi a ({new_i}, {new_j}) mosso nuovamente a ({new_i2}, {new_j2})")
                                        shield_walls = [(new_i2, new_j2, shield_unit) if s == closest_shield else s for s in shield_walls]
                    else:
                        print(f"Bot: Nessuna mossa valida per Muro di scudi a ({si}, {sj}) verso ({target_i}, {target_j})")

        # Fase 1: Attacchi
        for (i, j), unit in list(self.tablero.units.items()):
            if unit.owner != self.player2 or unit.has_attacked or unit.action_count >= getattr(unit, 'max_actions', 2):
                print(f"Bot: Ignoro unità a ({i}, {j}), proprietario: {unit.owner.Name}, has_attacked: {unit.has_attacked}, action_count: {unit.action_count}")
                continue
            nearest_enemy = min(enemy_units, key=lambda pos: abs(pos[0] - i) + abs(pos[1] - j))
            print(f"Bot: Unità {unit.__class__.__name__} a ({i}, {j}), nemico più vicino: {nearest_enemy}")
            original_orientation = unit.orientation
            best_attack = None
            for orientation in [1, 2, 3, 4]:
                unit.setOrientation(orientation)
                attack_positions = unit.get_attacks(self.tablero)
                print(f"Bot: Orientamento {orientation}, attacchi possibili: {attack_positions}")
                for pos in attack_positions:
                    target = self.tablero.cell_at(pos[0], pos[1])
                    if target and target.isUnit and target.owner == self.player1:
                        attack_value = 100 if target.isKing else 50 if target.__class__.__name__ == "knight" else 40 if target.__class__.__name__ == "archer" else 30
                        print(f"Bot: Trovato bersaglio valido a {pos}: {target.__class__.__name__}, valore attacco: {attack_value}")
                        if best_attack is None or attack_value > best_attack[2]:
                            best_attack = (orientation, target, attack_value)
            if best_attack:
                orientation, target, _ = best_attack
                unit.setOrientation(orientation)
                dice_count = unit.get_dice_count(target)
                dice_results = [random.randint(1, 3) for _ in range(dice_count)]
                print(f"Bot: Attacco con {dice_count} dadi: {dice_results}")
                success, winner = self.perform_attack(unit, target, dice_results)
                if success:
                    print(f"Bot: Attacco completato")
                    if hasattr(self, 'game_view'):
                        self.game_view.table.update_cell(target.i, target.j)
                    if winner:
                        print(f"Bot: Vittoria di {winner.Name}")
                        if hasattr(self, 'game_view'):
                            self.game_view.show_victory(winner)
                        return
            else:
                print(f"Bot: Nessun attacco valido trovato per {unit.__class__.__name__} a ({i}, {j})")
                unit.setOrientation(original_orientation)

        # Fase 2: Movimento (escludo Muri di scudi già mossi in modalità esperto)
        for (i, j), unit in list(self.tablero.units.items()):
            if unit.owner != self.player2 or unit.has_moved or unit.action_count >= getattr(unit, 'max_actions', 2):
                print(f"Bot: Ignoro movimento unità a ({i}, {j}), has_moved: {unit.has_moved}, action_count: {unit.action_count}")
                continue
            if self.expert and unit.__class__.__name__ == "shield_wall":
                print(f"Bot: Muro di scudi a ({i}, {j}) già gestito nella fase di protezione")
                continue
            nearest_enemy = min(enemy_units, key=lambda pos: abs(pos[0] - i) + abs(pos[1] - j))
            print(f"Bot: Unità {unit.__class__.__name__} a ({i}, {j}), nemico più vicino: {nearest_enemy}")
            best_orientation = get_best_orientation((i, j), nearest_enemy)
            new_i, new_j = self.find_closest_valid_move(i, j, nearest_enemy[0], nearest_enemy[1], unit.movements)
            if new_i is not None and new_j is not None:
                if self.move_unit(unit, new_i, new_j):
                    unit.setOrientation(best_orientation)
                    print(f"Bot: Unità {unit.__class__.__name__} mossa a ({new_i}, {new_j})")
                    if not unit.has_attacked:
                        attack_positions = unit.get_attacks(self.tablero)
                        print(f"Bot: Verifico attacchi post-movimento: {attack_positions}")
                        for pos in attack_positions:
                            target = self.tablero.cell_at(pos[0], pos[1])
                            if target and target.isUnit and target.owner == self.player1:
                                dice_count = unit.get_dice_count(target)
                                dice_results = [random.randint(1, 3) for _ in range(dice_count)]
                                print(f"Bot: Attacco post-movimento con {dice_count} dadi: {dice_results}")
                                success, winner = self.perform_attack(unit, target, dice_results)
                                if success:
                                    print(f"Bot: Attacco post-movimento completato")
                                    if hasattr(self, 'game_view'):
                                        self.game_view.table.update_cell(target.i, target.j)
                                    if winner:
                                        print(f"Bot: Vittoria di {winner.Name}")
                                        if hasattr(self, 'game_view'):
                                            self.game_view.show_victory(winner)
                                        return
                                    break
            else:
                print(f"Bot: Nessuna mossa valida trovata per {unit.__class__.__name__} a ({i}, {j})")

        print("Bot: Fine del turno")
