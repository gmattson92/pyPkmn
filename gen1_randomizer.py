import battle


def main():
    print('Welcome to pyPkmn!')
    print('Starting your battle...')
    bat = battle.Battle()
    while not bat.is_over:
        bat.turn()
    print('Thanks for playing!')


if __name__ == '__main__':
    main()
