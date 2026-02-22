import globals
from statusmanager import StatusManager
from move import Move
from ui import post_message
import sys
import random
from math import sqrt


class Pokemon:
    """
    Define characteristics of a Pokemon, including name, type(s),
    stats, movepool, and level
    """

    def __init__(self, name, moves='random', level=None):
        d = globals.get_species_dict(name)
        for key, value in d.items():
            setattr(self, key, value)
        if level:
            self.level = level
        else:
            self.level = self.randomizer_level
        self.DVs = [globals.MAX_DV] * globals.NUM_PERM_STATS
        self.stat_exp = [globals.MAX_STAT_EXP] * globals.NUM_PERM_STATS
        self.stat_stages = [0] * globals.NUM_BATTLE_STATS
        self.base_stats = [0] * globals.NUM_PERM_STATS
        self.fill_base_stats()
        self.stats = [0] * (globals.NUM_PERM_STATS - 1)
        """
        self.prz_flag = False
        self.brn_flag = False
        """
        self.max_hp = self.calc_stat(0)
        self._current_hp = self.max_hp
        """
        self.attack = self.calc_stat(1)
        self.defense = self.calc_stat(2)
        self.speed = self.calc_stat(3)
        self.special = self.calc_stat(4)
        """
        # Non-volatile status needed before calculating stats (BRN/PRZ debuff)
        self.sm = StatusManager(self)
        self.recalc_stats()
        # Replace randomize_moves with more general init_moves
        # self.moves = self.randomize_moves()
        self.moves = self.init_moves(moves)
        self.seen_moves = set()
        self._last_used_move_index = -1

    def is_fainted(self):
        if self.current_hp <= 0:
            self.sm.status = 'FNT'
            return True
        else:
            return False

    @property
    def current_hp(self):
        return self._current_hp

    @current_hp.setter
    def current_hp(self, val):
        if val < 0:
            self._current_hp = 0
        elif val > self.max_hp:
            self._current_hp = self.max_hp
        else:
            self._current_hp = val

    @property
    def attack(self):
        return self.stats[0]

    @attack.setter
    def attack(self, val):
        self.stats[0] = val

    @property
    def defense(self):
        return self.stats[1]

    @property
    def speed(self):
        return self.stats[2]

    @speed.setter
    def speed(self, val):
        self.stats[2] = val

    @property
    def special(self):
        return self.stats[3]

    def fill_base_stats(self):
        self.base_stats[0] = self.base_hp
        self.base_stats[1] = self.base_att
        self.base_stats[2] = self.base_def
        self.base_stats[3] = self.base_spe
        self.base_stats[4] = self.base_spc

    def calc_stat(self, index, crit=False):
        base = self.base_stats[index]
        dv = self.DVs[index]
        stat_exp = self.stat_exp[index]
        stat = int(((base + dv) * 2 + int(sqrt(stat_exp) / 4))
                   * self.level / 100) + 5
        # Max HP behaves a little differently
        if index == 0:
            stat += self.level + 5
        # Apply stage modifier, except for critical hits
        stage_multiplier = globals.get_stat_multiplier(self.stat_stages[index])
        if not crit:
            stat = int(stat * stage_multiplier)

        """
        # Removed -- status debuff has its own function now
        if index == 1 and self.brn_flag and not crit:
            stat = stat//2

        if index == 3 and self.prz_flag:
            stat = stat//4
        """

        return stat

    def recalc_stats(self):
        """
        self.attack = self.calc_stat(1)
        self.defense = self.calc_stat(2)
        self.speed = self.calc_stat(3)
        self.special = self.calc_stat(4)
        """
        for i in range(4):
            self.stats[i] = self.calc_stat(i+1)
        self.apply_status_debuff()

    def apply_status_debuff(self):
        """
        Apply the Attack (Speed) stat debuff caused by BRN (PRZ)
        """
        if self.sm.status not in ['BRN', 'PRZ']:
            return
        elif self.sm.status == 'BRN':
            new = self.attack // 2
            self.attack = new if new > 0 else 1
            return
        else:
            new = self.speed // 4
            self.speed = new if new > 0 else 1
            return

    def reset_stat_stages(self):
        self.stat_stages = [0] * globals.NUM_BATTLE_STATS

    def init_moves(self, moves):
        if moves == 'random':
            return self.randomize_moves()
        elif type(moves) == list:
            if len(moves) <= 4:
                return [Move(move) for move in moves]
            else:
                raise ValueError(f'Invalid starting move list {moves} '
                                 'is too long')
        else:
            raise ValueError(f'Invalid starting moves {moves}; should be list '
                             'or "random"')

    def randomize_moves(self):
        moves = []
        try:
            selected = random.sample(self.movepool, 4)
        except ValueError:
            selected = self.movepool
        for name in selected:
            try:
                moves.append(Move(name))
            except KeyError as e:
                print(f'randomize_moves(): name = {name} not found\n{e}')
                sys.exit(1)
        return moves

    def add_seen_move(self, move):
        self.seen_moves.add(move)

    @property
    def last_used_move_index(self):
        return self._last_used_move_index

    @last_used_move_index.setter
    def last_used_move_index(self, val):
        self._last_used_move_index = val

    def retreat(self):
        """
        Resets stat stages and status flags when Pokemon swaps out.
        """
        self.reset_stat_stages()
        self.sm.retreat()
        self.recalc_stats()

    def print_status(self):
        if globals.UI == 'text':
            post_message(f'{self.name} '
                         f'HP: {self.current_hp}/{self.max_hp}, '
                         f'Status: {self.sm.status}',
                         end='\n', wait=False)
        else:
            pass

    def print_moves(self, indent=True, seen_moves=False):
        if globals.UI == 'text':
            moves = self.seen_moves if seen_moves else self.moves
            if not moves:
                return False
            else:
                for i, move in enumerate(moves):
                    message = '--> ' if indent else ''
                    message += f'{i+1}. {move.name} ({move.pp}/{move.max_pp})'
                    post_message(message, end=' ', wait=False)
                return True
        else:
            pass

    def print_stats(self):
        if globals.UI == 'text':
            names = ['Att', 'Def', 'Spe', 'Spc']
            message = ''
            for i in range(4):
                message += (f'{names[i]}: {self.stats[i]} '
                            f'({self.stat_stages[i+1]:+d})\n')
            post_message(message, end='', wait=False)

    def print(self, show_stats=False, newline=True,
              indent_moves=True, seen_moves=False):
        self.print_status()
        if show_stats:
            self.print_stats()
        printed_moves = self.print_moves(indent=indent_moves,
                                         seen_moves=seen_moves)
        if globals.UI == 'text' and newline and printed_moves:
            post_message(wait=False)
