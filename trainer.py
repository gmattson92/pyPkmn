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
        self.active = self.party[0]

    @property
    def party_alive(self):
        pa = []
        for pkmn in self.party:
            if not pkmn.is_fainted():
                pa.append(pkmn)
        return pa

    def all_fainted(self):
        return len(self.party_alive) == 0

    def print(self):
        p = len(self.party)
        pa = len(self.party_alive)
        print(f'Trainer {self.name}:', end=' ')
        print(f'Overall status: {p-pa}/{p} Pokemon fainted. Details:')
        for i, pkmn in enumerate(self.party_alive):
            print(f'{i+1}.')
            pkmn.print(show_stats=True)

    def print_active(self):
        print(f'Trainer {self.name}\'s active Pokemon:')
        self.active.print()
