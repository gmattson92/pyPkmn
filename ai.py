import random


class AI:
    def __init__(self, algorithm, trainer, other):
        self.algorithm = algorithm
        self.trainer = trainer
        self.other = other

    def get_action(self):
        if self.algorithm == 'human':
            return self.human_get_action()
        elif self.algorithm == 'random':
            return self.random_get_action()
        else:
            return ('none', -1)

    def get_swap(self):
        if self.algorithm == 'human':
            return self.human_get_swap()
        elif self.algorithm == 'random':
            return self.random_get_swap()
        else:
            return ('swap', -1)

    def human_get_swap(self):
        print('Choose a Pokemon:')
        self.trainer.print()
        i = int(input())
        return ('swap', i-1)

    def human_get_action(self):
        print('What will you do?')
        val = int(input('1. Use move\n2. Swap\n'))
        if val == 1:
            print('Choose a move:')
            self.trainer.active.print()
            i = int(input())
            return ('move', i-1)
        elif val == 2:
            return self.human_get_swap()
        else:
            raise ValueError(f'Invalid choice {val}!')

    def random_get_swap(self):
        pa = len(self.trainer.party_alive)
        index = random.randrange(pa)
        return ('swap', index)

    def random_get_action(self):
        m = len(self.trainer.active.moves)
        index = random.randrange(m)
        return ('move', index)
