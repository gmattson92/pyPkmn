# import globals
from ui import get_UI
import random


def get_AI(ai_type, trainer, other):
    if ai_type == 'human':
        return HumanAI(trainer, other)
    elif ai_type == 'random':
        return RandomAI(trainer, other)
    else:
        raise ValueError(f'Invalid AI type {ai_type} !')


class AI:
    def __init__(self, trainer, other):
        self.trainer = trainer
        self.other = other

    def get_action(self):
        pass

    def get_swap(self):
        pass


class HumanAI(AI):
    def __init__(self, trainer, other):
        super().__init__(trainer, other)
        self.ui = get_UI(trainer)

    def get_action(self):
        return self._human_get_action()

    def get_swap(self):
        return self._human_get_swap()

    def _human_get_action(self):
        return self.ui.get_valid_action()

    def _human_get_swap(self):
        i = self.ui.get_valid_swap(False)
        return ('swap', i-1)


class RandomAI(AI):
    def __init__(self, trainer, other):
        super().__init__(trainer, other)

    def get_action(self):
        return self._random_get_action()

    def get_swap(self):
        return self._random_get_swap()

    def _random_get_swap(self):
        while True:
            index = random.randrange(len(self.trainer.party))
            if self.trainer.party[index] == self.trainer.active:
                continue
            elif self.trainer.party[index].is_fainted():
                continue
            else:
                break
        return ('swap', index)

    def _random_get_action(self):
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
