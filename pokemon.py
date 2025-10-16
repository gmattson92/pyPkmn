import globals
from move import Move
import random
import numpy as np


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
        self.sleep_turns = 0
        self.max_hp = self.calc_stat(0)
        self.current_hp = self.max_hp
        # self.attack = self.calc_stat(1)
        # self.defense = self.calc_stat(2)
        # self.speed = self.calc_stat(3)
        # self.special = self.calc_stat(4)
        self.recalc_stats()
        self.status = None
        self.moves = self.randomize_moves()

    def is_fainted(self):
        return self.current_hp <= 0

    def calc_stat(self, index):
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
        stat = int(((base + dv) * 2 + int(np.sqrt(stat_exp) / 4))
                   * self.level / 100) + 5
        stage_multiplier = globals.get_stat_multiplier(self.stat_stages[index])
        stat *= stage_multiplier
        if index == 0:
            stat += self.level + 5

        if index == 1 and self.brn_flag:
            stat = stat//2

        if index == 3 and self.prz_flag:
            stat = stat//4

        return stat

    def recalc_stats(self):
        self.attack = self.calc_stat(1)
        self.defense = self.calc_stat(2)
        self.speed = self.calc_stat(3)
        self.special = self.calc_stat(4)

    def randomize_moves(self):
        moves = []
        movepool = self.movepool.split(';')
        try:
            selected = random.sample(movepool, 4)
        except ValueError:
            selected = movepool
        for name in selected:
            try:
                moves.append(Move(name))
            except ValueError:
                moves.append(Move('Body Slam'))
        return moves

    def print_status(self):
        print(f'{self.name} '
              f'HP: {self.current_hp}/{self.max_hp}, '
              f'Status: {self.status}')

    def print_moves(self):
        for i, move in enumerate(self.moves):
            print(f'{i+1}. {move.name} ({move.pp}/{move.max_pp})',
                  end=' ')
        print()

    def print_stats(self):
        print(f'Att: {self.attack}, Def: {self.defense}, '
              f'Spe: {self.speed}, Spc: {self.special}')

    def print(self, show_stats=False):
        self.print_status()
        if show_stats:
            self.print_stats()
        self.print_moves()
