import globals
from pokemon import Pokemon
from ui import post_message
import random


class Trainer:
    """
    """

    def __init__(self, name, party_size=2, party='random'):
        self.name = name
        self.party = self.init_party(party, party_size)
        self._active = self.party[0]

    def init_party(self, party, party_size):
        ret = []
        if party == 'random':
            try:
                ret = [Pokemon(species) for species in
                       random.sample(globals.species_list, party_size)]
            except ValueError:
                ret = [Pokemon('Tauros')] * party_size
        elif type(party) == dict:
            # Assume keys are species, and values are tuples of level, moveset
            for species, tup in party.items():
                ret.append(Pokemon(species, tup[1], tup[0]))
        else:
            raise ValueError(f'Invalid starting party {party}; should be dict '
                             'or "random"')
        return ret

    @property
    def party_alive(self):
        pa = []
        for pkmn in self.party:
            if not pkmn.is_fainted():
                pa.append(pkmn)
        return pa

    @property
    def active(self):
        return self._active

    @active.setter
    def active(self, index):
        if self._active == self.party[index]:
            raise ValueError('Trying to swap to Pokemon already out! '
                             f'(index = {index})')
        elif self.party[index].is_fainted():
            raise ValueError('Trying to swap to a fainted Pokemon! '
                             f'(index = {index})')
        else:
            self._active.retreat()
            self._active = self.party[index]
            self._active.reset_stat_stages()
            self._active.recalc_stats()

    def all_fainted(self):
        return len(self.party_alive) == 0

    def print(self, stats=False, seen_moves=False):
        if globals.UI == 'text':
            p = len(self.party)
            pa = len(self.party_alive)
            post_message(f'Trainer {self.name}:', end=' ', wait=False)
            post_message(f'Overall status: {p-pa}/{p} Pokemon fainted. '
                         'Details:', wait=False)
            for i, pkmn in enumerate(self.party):
                post_message(f'{i+1}.', end=' ', wait=False)
                nl = False if pkmn == self.party[-1] else True
                pkmn.print(show_stats=stats, newline=nl,
                           indent_moves=True, seen_moves=seen_moves)
            post_message(end='')
        else:
            pass

    def print_active(self, stats=False, seen_moves=False):
        if globals.UI == 'text':
            post_message(f'Trainer {self.name}\'s active Pokemon:', wait=False)
            self.active.print(show_stats=stats, seen_moves=seen_moves)
        else:
            pass
