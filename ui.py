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


def get_valid_action(trainer):
    if globals.UI == 'text':
        return get_valid_text_action(trainer)
    else:
        pass


def get_valid_text_action(trainer):
    bad_input_message = 'Enter a valid number (1-3)'
    while True:
        try:
            post_message('What will you do?', wait=False)
            x = int(input('1. Fight\n2. Swap\n3. View party\n'))
            if x not in [1, 2, 3]:
                post_message(bad_input_message, wait=False)
                continue
            elif x == 2 and len(trainer.party_alive) == 1:
                post_message('You have no other Pokemon to send out! '
                             'Fight instead!', wait=False)
                continue
            else:
                # valid choice
                if x == 1:
                    total_pp = sum([move.pp for move in trainer.active.moves])
                    if total_pp == 0:
                        action = ('move', 4)
                        break
                    if trainer.active.sm.can_select_move:
                        post_message('Choose a move '
                                     '(enter 0 for previous menu):',
                                     wait=False)
                        # self.trainer.active.print()
                        i = get_valid_move(trainer)
                        if i == 0:
                            continue
                        else:
                            action = ('move', i-1)
                            break
                    else:
                        move = trainer.active.last_used_move
                        action = ('move', move)
                        break
                elif x == 2:
                    # post_message('Choose a Pokemon'
                    #              '(enter 0 for previous menu):',
                    #              wait=False)
                    # self.trainer.print()
                    i = get_valid_text_swap(trainer)
                    if i == 0:
                        continue
                    else:
                        action = ('swap', i-1)
                        break
                else:
                    trainer.print(stats=True)
                    post_message()
                    continue
        except ValueError:
            post_message(bad_input_message, wait=False)
            continue
    return action


def get_valid_move(trainer):
    if globals.UI == 'text':
        return get_valid_text_move(trainer)
    else:
        pass


def get_valid_text_move(trainer):
    total_pp = sum([move.pp for move in trainer.active.moves])
    if total_pp == 0:
        return 5
    bad_input_message = 'Enter a valid number'
    trainer.active.print()
    n_moves = len(trainer.active.moves)
    while True:
        try:
            x = int(input())
            if x == 0:
                break
            if x not in range(1, n_moves+1):
                post_message(bad_input_message, wait=False)
                continue
            elif trainer.active.moves[x-1].pp == 0:
                post_message('That move is out of PP! '
                             'Choose a different move.')
                continue
            else:
                break
        except ValueError:
            post_message(bad_input_message, wait=False)
            continue
    return x


def get_valid_swap(trainer, can_go_back=True):
    if globals.UI == 'text':
        return get_valid_text_swap(trainer, can_go_back)
    else:
        pass


def get_valid_text_swap(trainer, can_go_back=True):
    bad_input_message = 'Enter a valid number'
    trainer.print()
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
            if x not in range(1, len(trainer.party)+1):
                post_message(bad_input_message, wait=False)
                continue
            elif trainer.party[x-1] == trainer.active:
                post_message(f'{trainer.active.name} is already out! '
                             'Choose a different Pokemon.', wait=False)
                continue
            elif trainer.party[x-1].is_fainted():
                post_message(f'{trainer.party[x-1].name} is fainted! '
                             'Choose a different Pokemon.', wait=False)
                continue
            else:
                break
        except ValueError:
            post_message(bad_input_message, wait=False)
            continue
    return x
