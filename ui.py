import globals


def post_message(*args, **kwargs):
    if globals.UI == 'text':
        wait = True
        if 'wait' in kwargs:
            wait = kwargs.pop('wait')
        if 'end' not in kwargs:
            if wait:
                kwargs['end'] = ''
            else:
                kwargs['end'] = '\n'
        print(*args, **kwargs)
        if wait:
            input()
    else:
        pass


def get_UI(trainer):
    if globals.UI == 'text':
        return TextUI(trainer)
    elif globals.UI == 'gui':
        return GraphicalUI(trainer)
    else:
        raise ValueError(f'Invalid UI type {globals.UI} !')


class UI:
    def __init__(self, trainer):
        self._trainer = trainer

    def get_valid_action(trainer):
        pass

    def get_valid_move(self):
        pass

    def get_valid_swap(self):
        pass


class TextUI(UI):
    def __init__(self, trainer):
        super().__init__(trainer)

    def get_valid_action(self):
        return self._get_valid_text_action()

    def get_valid_move(self):
        return self._get_valid_text_move()

    def get_valid_swap(self, can_go_back=True):
        return self._get_valid_text_swap(can_go_back)


    def _get_valid_text_action(self):
        bad_input_message = 'Enter a valid number (1-3)'
        while True:
            try:
                post_message('What will you do?', wait=False)
                x = int(input('1. Fight\n2. Swap\n3. View party\n'))
                if x not in [1, 2, 3]:
                    post_message(bad_input_message, wait=False)
                    continue
                elif x == 2 and len(self._trainer.party_alive) == 1:
                    post_message('You have no other Pokemon to send out! '
                                 'Fight instead!', wait=False)
                    continue
                else:
                    # valid choice
                    if x == 1:
                        if self._trainer.active.sm.can_select_move:
                            post_message('Choose a move '
                                        '(enter 0 for previous menu):',
                                        wait=False)
                            i = self.get_valid_move()
                            if i == 0:
                                continue
                            else:
                                action = ('move', i-1)
                                break
                        else:
                            i = self._trainer.active.last_used_move_index
                            action = ('move', i)
                            break
                    elif x == 2:
                        i = self.get_valid_swap()
                        if i == 0:
                            continue
                        else:
                            action = ('swap', i-1)
                            break
                    else:
                        self._trainer.print(stats=True)
                        post_message()
                        continue
            except ValueError:
                post_message(bad_input_message, wait=False)
                continue
        return action


    def _get_valid_text_move(self):
        total_pp = sum([move.pp for move in self._trainer.active.moves])
        if total_pp == 0:
            return 5
        bad_input_message = 'Enter a valid number'
        self._trainer.active.print()
        n_moves = len(self._trainer.active.moves)
        while True:
            try:
                x = int(input())
                if x == 0:
                    break
                if x not in range(1, n_moves+1):
                    post_message(bad_input_message, wait=False)
                    continue
                elif self._trainer.active.moves[x-1].pp == 0:
                    post_message('That move is out of PP! '
                                'Choose a different move.')
                    continue
                else:
                    break
            except ValueError:
                post_message(bad_input_message, wait=False)
                continue
        return x


    def _get_valid_text_swap(self, can_go_back):
        bad_input_message = 'Enter a valid number'
        self._trainer.print()
        while True:
            try:
                if can_go_back:
                    post_message('Choose a Pokemon (enter 0 for previous menu):',
                                wait=False)
                else:
                    post_message('Choose a Pokemon:', wait=False)
                x = int(input())
                if x == 0:
                    if can_go_back:
                        break
                    else:
                        post_message('You must choose a new Pokemon!')
                        continue
                if x not in range(1, len(self._trainer.party)+1):
                    post_message(bad_input_message, wait=False)
                    continue
                elif self._trainer.party[x-1] == self._trainer.active:
                    post_message(f'{self._trainer.active.name} is already out!'
                                 ' Choose a different Pokemon.', wait=False)
                    continue
                elif self._trainer.party[x-1].is_fainted():
                    post_message(f'{self._trainer.party[x-1].name} is fainted!'
                                 ' Choose a different Pokemon.', wait=False)
                    continue
                else:
                    break
            except ValueError:
                post_message(bad_input_message, wait=False)
                continue
        return x


class GraphicalUI(UI):
    pass
