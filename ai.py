import ui
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
        # self.trainer.print()
        i = ui.get_valid_text_swap(self.trainer)
        return ('swap', i-1)

    def human_get_action(self):
        print('What will you do?')
        val = ui.get_valid_action(self.trainer)
        if val == 1:
            print('Choose a move:')
            # self.trainer.active.print()
            i = ui.get_valid_move(self.trainer)
            return ('move', i-1)
        elif val == 2:
            return self.human_get_swap()
        else:
            raise ValueError(f'Invalid choice {val}!')

    def random_get_swap(self):
        pa = len(self.trainer.party_alive)
        while True:
            index = random.randrange(pa)
            if self.trainer.party_alive[index] == self.trainer.active:
                continue
            else:
                break
        return ('swap', index)

    def random_get_action(self):
        total_pp = sum([move.pp for move in self.trainer.active.moves])
        if total_pp > 0:
            m = len(self.trainer.active.moves)
            while True:
                index = random.randrange(m)
                if self.trainer.active.moves[index].pp == 0:
                    continue
                else:
                    break
            return ('move', index)
        else:
            return ('move', -1)
