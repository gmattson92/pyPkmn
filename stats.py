import globals
from math import sqrt

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
    return stage_multipliers[int(stage)]


def get_evasion_multiplier(stage):
    return stage_multipliers[-1 * int(stage)]


class StatStage:
    """
    Define behavior of stat stages, used by Attack, Defense, Speed, Special,
    Accuracy and Evasion.
    """

    def __init__(self):
        self._value = 0

    def __int__(self):
        return self.value

    @property
    def value(self):
        return self._value

    @value.setter
    def value(self, new_value):
        if type(new_value) != int:
            raise TypeError(f'Invalid stat stage {new_value}; doing nothing')
        if new_value > -7 and new_value < 7:
            self._value = new_value
        else:
            raise ValueError(f'Invalid stat stage {new_value}; doing nothing')

    def can_change(self, stage_delta):
        # Stat stages must be within [-6, 6]
        new_value = self.value + stage_delta
        if new_value > -7 and new_value < 7:
            return True
        else:
            return False

    def bad_change_message(self):
        if self.value < 0:
            return 'could not be lowered any more!'
        else:
            return 'could not be raised any more!'


class AbstractStat:
    """
    Define common interface for all battle stats.
    """

    def __init__(self):
        self._stage = StatStage()
        self._value = None

    @property
    def value(self):
        return self._value

    @value.setter
    def value(self, new_value):
        self._value = new_value

    @property
    def stage(self):
        return self._stage

    def calculate_stat(self):
        raise NotImplementedError('Cannot call calculate_stat from base class'
                                  'AbstractStat!')

    def can_change(self, stage_delta):
        # By default, only check if the new stage is valid
        return self.stage.can_change(stage_delta)

    def bad_change_message(self):
        return self.stage.bad_change_message()


class MajorStat(AbstractStat):
    """
    Define behavior of the four major stats: Attack, Defense, Speed and
    Special.
    """

    def __init__(self, base, level):
        super().__init__()
        self._base = base
        self._pkmn_lvl = level
        self._DV = globals.MAX_DV
        self._exp = globals.MAX_STAT_EXP
        self._value = self.calculate_stat()

    def __int__(self):
        return self.value

    @property
    def value(self):
        return self._value

    @value.setter
    def value(self, new_value):
        # Major stats must be integers within the [1, 999] range
        if type(new_value) == int and new_value > 0 and new_value < 1000:
            self._value = new_value
        else:
            raise ValueError(f'Invalid stat value {new_value}; doing nothing')

    def calculate_stat(self, crit=False, stage=None):
        # Basic formula
        stat = int(((self._base + self._DV) * 2 + int(sqrt(self._exp) / 4))
                   * self._pkmn_lvl / 100) + 5
        if not crit:
            # Apply stage modifier, except for critical hits
            if stage:
                stage_multiplier = get_stat_multiplier(stage)
            else:
                stage_multiplier = get_stat_multiplier(self._stage)
            stat = int(stat * stage_multiplier)
        return stat

    def can_change(self, stage_delta):
        # First check if the new stage is within [-6, 6]
        if not self.stage.can_change(stage_delta):
            return False
        # Next, the updated stat cannot lie outside [1, 999]
        new_stage = int(self.stage) + stage_delta
        new_value = self.calculate_stat(stage=new_stage)
        if new_value < 1 or new_value > 999:
            return False
        else:
            return True


class MaxHP(MajorStat):
    """
    Define behavior of the maximum HP stat, which is slightly different from
    the other major stats.
    """

    def __init__(self, base, level):
        # Note that super().__init__ uses **MaxHP.calculate_stat**
        # rather than MajorStat.calculate_stat
        super().__init__(base, level)

    def calculate_stat(self):
        # Start with the basic formula
        stat = super().calculate_stat(crit=False)
        # Max HP behaves a little differently
        stat += self._pkmn_lvl + 5
        return stat


class AccEvaStat(AbstractStat):
    """
    Define behavior of Accuracy/Evasion stats, which depend only on their
    stat stage.
    """

    def __init__(self, name):
        super().__init__()
        self._name = name
        self._value = self.calculate_stat()

    def calculate_stat(self):
        if self._name == 'acc':
            return get_stat_multiplier(int(self._stage))
        elif self._name == 'eva':
            return get_evasion_multiplier(int(self._stage))
        else:
            raise ValueError(f'Invalid name {self._name}')


class Stats:
    """
    Define interface to and behavior of a Pokemon's full set of battle stats.
    """

    def __init__(self, pkmn):
        self._pkmn = pkmn
        self._pkmn_lvl = pkmn._level
        self._base_stats = self._get_base_stats()
        self._stats = self._create_stat_objects()

    def __getitem__(self, subscript):
        if type(subscript) != int:
            raise TypeError(f'Invalid subscript {subscript}')
        if subscript < 0 or subscript > (len(self._stats) - 1):
            raise IndexError(f'Invalid subscript {subscript}')
        return self._stats[subscript].value

    @property
    def stats_l(self):
        return self._stats

    @property
    def max_hp(self):
        return self._stats[0]

    @property
    def attack(self):
        return self._stats[1]

    @property
    def defense(self):
        return self._stats[2]

    @property
    def speed(self):
        return self._stats[3]

    @property
    def special(self):
        return self._stats[4]

    @property
    def accuracy(self):
        return self._stats[5]

    @property
    def evasion(self):
        return self._stats[6]

    def get_stat_stages(self):
        return [int(so.stage) for so in self._stats]

    def reset_stat_stages(self):
        for so in self._stats:
            so.stage.value = 0

    def recalculate_one(self, index):
        """
        Recalculate (and update value of) one stat based on current stages.
        Does not apply BRN/PRZ debuff.
        """
        self._validate_index(index)
        so = self._stats[index]
        so.value = so.calculate_stat()

    def recalculate_all(self):
        """
        Recalculate and update all stats based on current stages and BRN/PRZ.
        """
        for i in range(1, globals.NUM_BATTLE_STATS):
            self.recalculate_one(i)
        self.apply_status_debuff()

    def apply_status_debuff(self):
        """
        Apply the Attack (Speed) stat debuff caused by BRN (PRZ).
        """
        if self._pkmn.sm.status not in ['BRN', 'PRZ']:
            return
        elif self._pkmn.sm.status == 'BRN':
            new = self.attack.value // 2
            self.attack.value = new if new > 0 else 1
            return
        else:
            new = self.speed.value // 4
            self.speed.value = new if new > 0 else 1
            return

    def can_change(self, index, stage_delta):
        self._validate_index(index)
        return self._stats[index].can_change(stage_delta)

    def get_bad_change_message(self, index):
        self._validate_index(index)
        message = f'{self._pkmn.name}\'s '
        message += f'{index_to_stat[index]} '
        message += self._stats[index].bad_change_message()
        return message

    def modify_stat(self, index, stage_delta):
        self._validate_index(index)
        if not self.can_change(index, stage_delta):
            # Safety check
            raise ValueError(f'Stat index {index} cannot be changed by '
                             f'delta = {stage_delta}')
        self._stats[index].stage.value += stage_delta
        self.recalculate_one(index)

    def get_modified_message(self, index, stage_delta):
        self._validate_index(index)
        message = f'{self._pkmn.name}\'s '
        message += f'{index_to_stat[index]} '
        sharply = ('sharply ' if abs(stage_delta) >= 2
                   else '')
        message += sharply
        message += ('increased!' if stage_delta > 0
                    else 'decreased!')
        return message

    def _get_base_stats(self):
        base_stats = []
        base_stats.append(self._pkmn.base_hp)
        base_stats.append(self._pkmn.base_att)
        base_stats.append(self._pkmn.base_def)
        base_stats.append(self._pkmn.base_spe)
        base_stats.append(self._pkmn.base_spc)
        return base_stats

    def _create_stat_objects(self):
        stat_objects = []
        stat_objects.append(MaxHP(self._base_stats[0], self._pkmn_lvl))
        stat_objects.append(MajorStat(self._base_stats[1], self._pkmn_lvl))
        stat_objects.append(MajorStat(self._base_stats[2], self._pkmn_lvl))
        stat_objects.append(MajorStat(self._base_stats[3], self._pkmn_lvl))
        stat_objects.append(MajorStat(self._base_stats[4], self._pkmn_lvl))
        stat_objects.append(AccEvaStat('acc'))
        stat_objects.append(AccEvaStat('eva'))
        return stat_objects

    def _validate_index(self, index):
        if type(index) != int or index not in range(1, 7):
            raise IndexError(f'Invalid stat index {index}')
