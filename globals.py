import pandas as pd
import random


MAX_DV = 15
MAX_STAT_EXP = 65535
NUM_PERM_STATS = 5
NUM_BATTLE_STATS = 7
FULL_PRZ_CHANCE = 25
MIN_SLP_TURNS = 1
MAX_SLP_TURNS = 7


def rng_check(pct_chance):
    x = random.random()
    if x <= (pct_chance/100):
        return True
    else:
        return False


def sleep_turns():
    return random.randrange(MIN_SLP_TURNS, MAX_SLP_TURNS+1)


# Define stat index mapping
index_to_stat = {0: 'HP', 1: 'Attack', 2: 'Defense', 3: 'Speed',
                 4: 'Special', 5: 'Accuracy', 6: 'Evasion'}
stat_to_index = {'HP': 0, 'Attack': 1, 'Defense': 2, 'Speed': 3,
                 'Special': 4, 'Accuracy': 5, 'Evasion': 6}

# Define stat stages mapping
stage_multipliers = {-6: 0.25, -5: 0.28, -4: 0.33, -3: 0.4, -2: 0.5,
                     -1: 0.66, 0: 1.0, 1: 1.5, 2: 2.0, 3: 2.5,
                     4: 3.0, 5: 3.5, 6: 4.0}


def get_stat_multiplier(stage):
    return stage_multipliers[stage]


def get_evasion_multiplier(stage):
    return stage_multipliers[-stage]


# Define global species data
species_df = pd.read_csv('species_list_testing.csv')
species_list = list(species_df['name'])


def get_species_dict(name):
    return species_df[species_df['name'] == name].to_dict(orient='records')[0]


# Define global moves data
moves_df = pd.read_csv('moves_list_testing.csv')
moves_list = list(moves_df['name'])


def get_moves_dict(name):
    return moves_df[moves_df['name'] == name].to_dict(orient='records')[0]


# Define global type interactions
# type_chart = {}
types = ['None', 'Normal', 'Fighting', 'Flying', 'Poison', 'Ground', 'Rock',
         'Bug', 'Ghost', 'Fire', 'Water', 'Grass', 'Electric', 'Psychic',
         'Ice', 'Dragon']
type_list = [
    [1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1],               # None
    [1, 1, 1, 1, 1, 1, 0.5, 1, 0, 1, 1, 1, 1, 1, 1, 1],             # Normal
    [1, 2, 1, 0.5, 0.5, 1, 2, 0.5, 0, 1, 1, 1, 1, 0.5, 2, 1],       # Fighting
    [1, 1, 2, 1, 1, 1, 0.5, 2, 1, 1, 1, 2, 0.5, 1, 1, 1],           # Flying
    [1, 1, 1, 1, 0.5, 0.5, 0.5, 2, 0.5, 1, 1, 2, 1, 1, 1, 1],       # Poison
    [1, 1, 1, 0, 2, 1, 2, 0.5, 1, 2, 1, 0.5, 2, 1, 1, 1, 1],        # Ground
    [1, 1, 0.5, 2, 1, 0.5, 1, 2, 1, 2, 1, 1, 1, 1, 2, 1],           # Rock
    [1, 1, 0.5, 0.5, 2, 1, 1, 1, 0.5, 0.5, 1, 2, 1, 2, 1, 1],       # Bug
    [1, 0, 1, 1, 1, 1, 1, 1, 2, 1, 1, 1, 1, 0, 1, 1],               # Ghost
    [1, 1, 1, 1, 1, 1, 0.5, 2, 1, 0.5, 0.5, 2, 1, 1, 2, 0.5],       # Fire
    [1, 1, 1, 1, 1, 2, 2, 1, 1, 2, 0.5, 0.5, 1, 1, 1, 0.5],         # Water
    [1, 1, 1, 0.5, 0.5, 2, 2, 0.5, 1, 0.5, 2, 0.5, 1, 1, 1, 0.5],   # Grass
    [1, 1, 1, 2, 1, 0, 1, 1, 1, 1, 2, 0.5, 0.5, 1, 1, 0.5],         # Electric
    [1, 1, 2, 1, 2, 1, 1, 1, 1, 1, 1, 1, 1, 0.5, 1, 1],             # Psychic
    [1, 1, 1, 2, 1, 2, 1, 1, 1, 1, 0.5, 2, 1, 1, 0.5, 2],           # Ice
    [1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 2]                # Dragon
]

type_dict = {}
for i, offensive in enumerate(types):
    d = {}
    for j, defensive in enumerate(types):
        d[defensive] = type_list[i][j]
    type_dict[offensive] = d


def get_type_mult(offensive, defensive):
    return type_dict[offensive][defensive]


if __name__ == '__main__':
    for offensive in type_dict.keys():
        print(f'Offensive = {offensive}')
        print(type_dict[offensive])
