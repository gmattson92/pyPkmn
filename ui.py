import globals


def post_message(message):
    if globals.UI == 'text':
        print(message)
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
            x = int(input('1. Use move\n2. Swap\n3. View party\n'))
            if x not in [1, 2, 3]:
                print(bad_input_message)
                continue
            elif x == 2 and len(trainer.party_alive) == 1:
                print('You have no other Pokemon to send out! '
                      'Use a move instead!')
                continue
            else:
                break
        except ValueError:
            print(bad_input_message)
            continue
    return x


def get_valid_move(trainer):
    if globals.UI == 'text':
        return get_valid_text_move(trainer)
    else:
        pass


def get_valid_text_move(trainer):
    bad_input_message = 'Enter a valid number'
    trainer.active.print()
    n_moves = len(trainer.active.moves)
    total_pp = sum([move.pp for move in trainer.active.moves])
    if total_pp == 0:
        return 0
    while True:
        try:
            x = int(input())
            if x == 0:
                break
            if x not in range(1, n_moves+1):
                print(bad_input_message)
                continue
            elif trainer.active.moves[x-1].pp == 0:
                print('That move is out of PP! Choose a different move.')
                continue
            else:
                break
        except ValueError:
            print(bad_input_message)
            continue
    return x


def get_valid_swap(trainer):
    if globals.UI == 'text':
        return get_valid_text_swap(trainer)
    else:
        pass


def get_valid_text_swap(trainer):
    bad_input_message = 'Enter a valid number'
    trainer.print()
    while True:
        try:
            x = int(input())
            if x == 0:
                return x
            if x not in range(1, len(trainer.party)+1):
                print(bad_input_message)
                continue
            elif trainer.party[x-1] == trainer.active:
                print(f'{trainer.active.name} is already out! '
                      'Choose a different Pokemon.')
                continue
            elif trainer.party[x-1].is_fainted():
                print(f'{trainer.party[x-1].name} is fainted! '
                      'Choose a different Pokemon.')
                continue
            else:
                break
        except ValueError:
            print(bad_input_message)
            continue
    return x
