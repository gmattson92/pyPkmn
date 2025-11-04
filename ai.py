# import globals
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
        # if globals.UI == 'text':
        #     ui.post_message('Choose a Pokemon:', wait=False)
        # self.trainer.print()
        i = ui.get_valid_swap(self.trainer, False)
        return ('swap', i-1)

    def human_get_action(self):
        return ui.get_valid_action(self.trainer)

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
            n = len(self.trainer.active.moves)
            while True:
                index = random.randrange(n)
                if self.trainer.active.moves[index].pp == 0:
                    continue
                else:
                    break
            return ('move', index)
        else:
            return ('move', 4)
