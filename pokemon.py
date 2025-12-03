import globals
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

    def __init__(self, name, level=None):
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
        self.prz_flag = False
        self.brn_flag = False
        self.max_hp = self.calc_stat(0)
        self._current_hp = self.max_hp
        # self.attack = self.calc_stat(1)
        # self.defense = self.calc_stat(2)
        # self.speed = self.calc_stat(3)
        # self.special = self.calc_stat(4)
        self.recalc_stats()
        self.status = None
        self.moves = self.randomize_moves()
        self.seen_moves = set()
        # now all the specific flags for status and move interactions:
        # status interactions
        self.sleep_turns = 0
        self.confused = False
        self.confused_turns = 0
        self.flinched = False
        self.disabled = False
        self.disabled_turns = 0
        self.seeded = False
        self.toxic = False
        self.toxic_N = 1
        # stat interactions
        self.lightscreen = False
        self.reflect = False
        # move selection disabled
        self.recharge = False
        self.two_turn = False
        self.multiturn = False
        self.multiturn_turns = 0
        self.trapping = False
        self.trapping_turns = 0
        self.trapped = False
        self.trapped_turns = 0

    def is_fainted(self):
        if self.current_hp <= 0:
            self.status = 'FNT'
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

    def calc_stat(self, index, crit=False):
        if index == 0:
            base = self.base_hp
        elif index == 1:
            base = self.base_att
        elif index == 2:
            base = self.base_def
        elif index == 3:
            base = self.base_spe
        elif index == 4:
            base = self.base_spc
        else:
            raise ValueError(f'Invalid index = {index}')

        dv = self.DVs[index]
        stat_exp = self.stat_exp[index]
        stat = int(((base + dv) * 2 + int(sqrt(stat_exp) / 4))
                   * self.level / 100) + 5
        stage_multiplier = globals.get_stat_multiplier(self.stat_stages[index])
        if not crit:
            stat *= stage_multiplier
        if index == 0:
            stat += self.level + 5

        if index == 1 and self.brn_flag and not crit:
            stat = stat//2

        if index == 3 and self.prz_flag:
            stat = stat//4

        return stat

    def recalc_stats(self):
        self.attack = self.calc_stat(1)
        self.defense = self.calc_stat(2)
        self.speed = self.calc_stat(3)
        self.special = self.calc_stat(4)

    def reset_stat_stages(self):
        self.stat_stages = [0] * globals.NUM_BATTLE_STATS

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

    def print_status(self):
        if globals.UI == 'text':
            post_message(f'{self.name} '
                         f'HP: {self.current_hp}/{self.max_hp}, '
                         f'Status: {self.status}',
                         end='\n', wait=False)
        else:
            pass

    def print_moves(self, indent=True, seen_moves=False):
        if globals.UI == 'text':
            moves = self.seen_moves if seen_moves else self.moves
            for i, move in enumerate(moves):
                message = '--> ' if indent else ''
                message += f'{i+1}. {move.name} ({move.pp}/{move.max_pp})'
                post_message(message, end=' ', wait=False)
        else:
            pass

    def print_stats(self):
        if globals.UI == 'text':
            post_message(f'Att: {self.attack}, Def: {self.defense}, '
                         f'Spe: {self.speed}, Spc: {self.special}',
                         end='\n', wait=False)
        else:
            pass

    def print(self, show_stats=False, newline=True,
              indent_moves=True, seen_moves=False):
        self.print_status()
        if show_stats:
            self.print_stats()
        self.print_moves(indent=indent_moves, seen_moves=seen_moves)
        if globals.UI == 'text' and newline:
            post_message(wait=False)
