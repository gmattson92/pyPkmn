import globals
import battle
import sys

# Define some pre-set parties for testing
# Modifying stat stages
d_statchanges = {
    'Cloyster': (100, ['Withdraw', 'Harden', 'Acid Armor', 'Roar']),
    'Shellder': (100, ['Leer', 'Screech', 'Acid Armor', 'Roar']),
    'Chansey': (1, ['Defense Curl', 'Roar']),
    'Porygon': (100, ['Agility', 'Sharpen', 'Harden', 'Amnesia'])
}


# Non-volatile status conditions
d_statuses = {
    'Bulbasaur': (5, ['PoisonPowder', 'Thunder Wave', 'Spore', 'Toxic']),
    'Caterpie': (5, ['Ember', 'Ice Beam', 'Ice Beam', 'Toxic']),
    'Chansey': (100, ['Rest', 'Roar']),
    'Koffing': (100, ['Roar'])
}


d_teams = {
    'statchanges': d_statchanges,
    'statuses': d_statuses  # ,
    # 'statusdebuffs': d_debuffs,
    # 'vstatuses': d_vstatuses,
}


def main():
    globals.DEBUG = True
    print('Welcome to pyPkmn Testing Mode!')
    print(f'Available test scenarios: {list(d_teams.keys())}')
    choice = input('Which scenario do you want?\n')
    team = {}
    try:
        team = d_teams[choice]
    except KeyError:
        print(f'Invalid choice {choice}; quitting!')
        sys.exit(1)
    print('Starting your battle...')
    bat = battle.Battle(trainer2_ai='human',
                        trainer1_party=team,
                        trainer2_party=team)
    while not bat.is_over:
        bat.round()
    print('Thanks for playing!')


if __name__ == '__main__':
    main()
