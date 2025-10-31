import globals
from pokemon import Pokemon
import random


class Trainer:
    """
    """

    def __init__(self, name, party_size=2):
        self.name = name
        try:
            self.party = [Pokemon(species) for species in
                          random.sample(globals.species_list, party_size)]
        except ValueError:
            self.party = [Pokemon('Tauros')] * party_size
        self._active = self.party[0]

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
        # self._active.reset_stat_stages()
        if self._active == self.party[index]:
            raise ValueError('Trying to swap to Pokemon already out! '
                             f'(index = {index})')
        elif self.party[index].is_fainted():
            raise ValueError('Trying to swap to a fainted Pokemon! '
                             f'(index = {index})')
        else:
            self._active = self.party[index]
            self._active.reset_stat_stages()
            self._active.recalc_stats()

    def all_fainted(self):
        return len(self.party_alive) == 0

    def print(self, stats=False):
        p = len(self.party)
        pa = len(self.party_alive)
        print(f'Trainer {self.name}:', end=' ')
        print(f'Overall status: {p-pa}/{p} Pokemon fainted. Details:')
        for i, pkmn in enumerate(self.party):
            print(f'{i+1}.')
            pkmn.print(show_stats=stats)

    def print_active(self):
        print(f'Trainer {self.name}\'s active Pokemon:')
        self.active.print()
