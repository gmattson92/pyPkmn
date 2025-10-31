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
        while True:
            print('What will you do?')
            val = ui.get_valid_action(self.trainer)
            if val == 1:
                print('Choose a move (enter 0 for previous menu):')
                # self.trainer.active.print()
                i = ui.get_valid_move(self.trainer)
                if i == 0:
                    continue
                else:
                    return ('move', i-1)
            elif val == 2:
                print('Choose a Pokemon (enter 0 for previous menu):')
                # self.trainer.print()
                i = ui.get_valid_text_swap(self.trainer)
                if i == 0:
                    continue
                else:
                    return ('swap', i-1)
            elif val == 3:
                self.trainer.print(stats=True)
                continue
            else:
                raise ValueError(f'Invalid choice {val}!')

    def random_get_swap(self):
        while True:
            index = random.randrange(len(self.trainer.party))
            if self.trainer.party[index] == self.trainer.active:
                continue
            elif self.trainer.party[index].is_fainted():
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
