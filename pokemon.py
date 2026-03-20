import globals
from mediator import Colleague
from statusmanager import StatusManager
from stats import Stats
from move import Move
from ui import post_message
import sys
import random


class Pokemon(Colleague):
    """
    Define characteristics of a Pokemon, including name, type(s),
    stats, moveset, and level
    """

    def __init__(self, name, moves='random', level=None):
        super().__init__()
        d = globals.get_species_dict(name)
        for key, value in d.items():
            setattr(self, key, value)
        self._level = level if level else self.randomizer_level
        # Non-volatile status needed before calculating stats (BRN/PRZ debuff)
        self.sm = StatusManager(self)
        # Main in-battle stats
        self.stats = Stats(self)
        self._current_hp = self.max_hp
        # Moveset
        self.moves = self._init_moves(moves)
        self.seen_moves = set()
        self._last_used_move_index = -1
        # Text UI printing
        self._printer = PkmnPrinter(self)

    def is_fainted(self):
        if self.current_hp == 0:
            return True
        else:
            return False

    @property
    def current_hp(self):
        return self._current_hp

    @current_hp.setter
    def current_hp(self, val):
        if val <= 0:
            self._current_hp = 0
            self.sm.status = 'FNT'
            post_message(f'{self.name} fainted!')
            self.send_event({'event_type': 'faint', 'pkmn': self})
        elif val > self.max_hp:
            self._current_hp = self.max_hp
        else:
            self._current_hp = val

    @property
    def max_hp(self):
        return self.stats[0]

    @property
    def attack(self):
        return self.stats[1]

    # @attack.setter
    # def attack(self, val):
    #     self.stats[0] = val

    @property
    def defense(self):
        return self.stats[2]

    @property
    def speed(self):
        return self.stats[3]

    # @speed.setter
    # def speed(self, val):
    #     self.stats[2] = val

    @property
    def special(self):
        return self.stats[4]

    @property
    def accuracy(self):
        return self.stats[5]

    @property
    def evasion(self):
        return self.stats[6]

    @property
    def level(self):
        return self._level

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
        self.stats.reset_stat_stages()
        self.sm.retreat()
        self.stats.recalculate_all()

    def receive_event(self, event_d):
        if event_d['event_type'] == 'faint':
            if event_d['pkmn'] != self:
                self.sm.opponent_fainted()
        elif event_d['event_type'] == 'swap':
            if event_d['trainer'].active != self:
                self.sm.opponent_swapped()
        elif event_d['event_type'] == 'hyper_beam_ko':
            if event_d['pkmn'] != self:
                self.sm.hyper_beam_ko()
        else:
            pass

    def _init_moves(self, moves):
        if moves == 'random':
            return self._randomize_moves()
        elif type(moves) == list:
            if len(moves) > 0 and len(moves) <= 4:
                return [Move(move) for move in moves]
            else:
                raise ValueError(f'Invalid starting move list {moves} -- '
                                 'must have between 1 and 4 moves')
        else:
            raise ValueError(f'Invalid starting moves {moves}; should be list '
                             'or "random"')

    def _randomize_moves(self):
        moves = []
        try:
            selected = random.sample(self.movepool, 4)
        except ValueError:
            selected = self.movepool
        for name in selected:
            try:
                moves.append(Move(name))
            except KeyError as e:
                print(f'_randomize_moves(): name = {name} not found\n{e}')
                sys.exit(1)
        return moves

    def print_status(self):
        self._printer.print_status()

    def print_moves(self, indent=True, seen_moves=False):
        return self._printer.print_moves(indent=indent, seen_moves=seen_moves)

    def print_stats(self):
        self._printer.print_stats()

    def print(self, show_stats=False, newline=True,
              indent_moves=True, seen_moves=False):
        self._printer.print(show_stats=show_stats, newline=newline,
                            indent_moves=indent_moves, seen_moves=seen_moves)


class PkmnPrinter:
    """
    Define functionality to print a Pokemon's overall status, stats, and move
    set.
    """

    def __init__(self, pkmn):
        self._pkmn = pkmn

    def print_status(self):
        if globals.UI == 'text':
            post_message(f'{self._pkmn.name} '
                         f'HP: {self._pkmn.current_hp}/{self._pkmn.max_hp}, '
                         f'Status: {self._pkmn.sm.status}',
                         end='\n', wait=False)
        else:
            pass

    def print_moves(self, indent=True, seen_moves=False):
        """
        Prints Pokemon's move set. Returns bool indicated whether anything
        was printed (since Pokemon's seen_moves can be empty at the start of
        the battle).
        """

        if globals.UI == 'text':
            moves = self._pkmn.seen_moves if seen_moves else self._pkmn.moves
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
            names = ['Max HP', 'Att', 'Def', 'Spe', 'Spc']
            stages = self._pkmn.stats.get_stat_stages()
            message = ''
            for i in range(1, 5):
                message += (f'{names[i]}: {self._pkmn.stats[i]} '
                            f'({stages[i]:+d})\n')
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
