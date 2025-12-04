import globals
from ui import post_message
import random


class MoveUser:
    """
    Handles all details of 'appyling' a move -- including damage, status, stat
    changes, and special effects of unique moves
    """

    def __init__(self):
        self.last_damage = 0

    def before_move(self, user):
        """
        Applies certain changes to Pokemon's status --
            - decrementing the sleep counter
            - checking if the Pokemon wakes up
            - decrementing the confusion counter
            - checking if the Pokemon snaps out of confusion
            - decrementing the Disable counter
            - checking if the Disable ends
            - resetting flinch and Hyper Beam recharge flags
        Returns bool whether the Pokemon can use a move this turn, or if it's
        prevented from moving by status, flinch, etc.
        """
        # Check non-volatile status
        can_move_status, fully_prz = self.can_move_status(user)

        # Check for flinching
        can_move_flinch = self.can_move_flinch(user)

        # Check for recharge turn
        can_move_recharge = self.can_move_recharge(user)

        # Check for trapping moves
        if user.trapped:
            can_move_trapped = False
            self.decrement_counter(user, 'trapped')
        else:
            can_move_trapped = True
        # Decrement trapping counter
        if user.trapping:
            self.decrement_counter(user, 'trapping')

        can_move_nonstatus = (can_move_flinch and can_move_recharge
                              and can_move_trapped)
        can_move = can_move_status and can_move_nonstatus

        # Confusion and Disable, which are paused  during sleep, freeze,
        # flinches, and recharge turns, but do decrement during full paralysis.
        decrement = can_move or (fully_prz and can_move_nonstatus)
        if decrement:
            if user.disabled:
                self.decrement_counter(user, 'disable')
            if user.confused:
                self.decrement_counter(user, 'confusion')

        # Multiturn, which is more complicated -- hits in confusion and full
        # paralysis reset the move completely; sleep, freeze and trapped all
        # pause the move but do not decrement the counter.
        do_not_decrement = user.status in ['SLP', 'FRZ'] or user.trapped
        reset = fully_prz
        if not do_not_decrement:
            if user.multiturn:
                self.decrement_counter(user, 'multiturn')
        if reset:
            if user.multiturn:
                while True:
                    try:
                        self.decrement_counter(user, 'multiturn')
                    except:
                        break


        return can_move

    def can_move_status(self, pkmn):
        """
        Checks if pkmn is prevented from moving by a non-volatile status
        condition and, if so, posts the appropriate message. Also handles
        decrementing the sleep counter.
        Returns (can_move, fully_paralyzed). The latter is needed for deciding
        whether or not to decrement the confusion and disable counters.
        """
        # Confusion and Disable counters are a little complicated, so we need
        # the following flag to check whether they should decrement
        fully_prz = False
        # Now check for status conditions
        if pkmn.status == 'SLP':
            can_move_status = False
            self.decrement_counter(pkmn, 'sleep')
        elif pkmn.status == 'FRZ':
            post_message(f'{pkmn.name} is frozen solid!')
            can_move_status = False
        elif pkmn.status == 'PRZ':
            fully_prz = globals.rng_check(globals.FULL_PRZ_CHANCE)
            if fully_prz:
                post_message(f'{pkmn.name} is fully paralyzed!')
                can_move_status = False
            else:
                can_move_status = True
        else:
            can_move_status = True

        return (can_move_status, fully_prz)

    def can_move_flinch(self, pkmn):
        if pkmn.flinched:
            post_message(f'{pkmn.name} flinched!')
            # Reset the flinch flag
            pkmn.flinched = False
            can_move_flinch = False
        else:
            can_move_flinch = True
        return can_move_flinch

    def can_move_recharge(self, pkmn):
        if pkmn.recharge:
            can_move_recharge = False
            post_message(f'{pkmn.name} has to recharge!')
            # Reset the recharge flag, unless pkmn is frozen
            if pkmn.status != 'FRZ':
                pkmn.recharge = False
        else:
            can_move_recharge = True
        return can_move_recharge

    def decrement_counter(self, pkmn, which):
        d = {'sleep': {'cnd': (pkmn.status == 'SLP'),   # condition
                       'cnt': 'sleep_turns',            # counter attribute
                       'att': 'status',                 # attribute to update
                       'val': None,                     # new value
                       'cm': 'is fast asleep!',         # condition message
                       'rcm': 'woke up!'},              # removed condition msg
             'confusion': {'cnd': pkmn.confused,
                           'cnt': 'confused_turns',
                           'att': 'confused',
                           'val': False,
                           'cm': 'is confused!',
                           'rcm': 'snapped out of confusion!'},
             'disable': {'cnd': pkmn.disabled,
                         'cnt': 'disabled_turns',
                         'att': 'disabled',
                         'val': False,
                         'cm': 'is disabled!',
                         'rcm': 'is no longer disabled!'},
             'trapped': {'cnd': pkmn.trapped,
                         'cnt': 'trapped_turns',
                         'att': 'trapped',
                         'val': False,
                         'cm': 'cannot move!',
                         'rcm': 'was released!'},
             'trapping': {'cnd': pkmn.trapping,
                          'cnt': 'trapping_turns',
                          'att': 'trapping',
                          'val': False,
                          'cm': '',
                          'rcm': ''},
             'multiturn': {'cnd': pkmn.multiturn,
                           'cnt': 'multiturn_turns',
                           'att': 'multiturn',
                           'val': False,
                           'cm': '',
                           'rcm': ''}}

        implemented_conditions = ['sleep', 'confusion', 'disable',
                                  'trapped', 'trapping', 'multiturn']
        if which not in implemented_conditions:
            raise ValueError(f'In decrement_counter(): invalid which={which}')

        condition_applies = d[which]['cnd']
        counter_attr = d[which]['cnt']
        attr_to_update = d[which]['att']
        updated_val = d[which]['val']
        condition_message = d[which]['cm']
        removed_condition_message = d[which]['rcm']

        current_attr = getattr(pkmn, attr_to_update)
        current_counter_val = getattr(pkmn, counter_attr)
        if not condition_applies:
            raise ValueError(f'In decrement_counter(): condition does not '
                             f'apply! Details:\nname={pkmn.name}, '
                             f'which={which}, attr={current_attr}, '
                             f'counter={current_counter_val}')
        # Double check that the counter is nonzero
        if current_counter_val < 1:
            raise ValueError(f'In decrement_counter(): condition applies but '
                             f'counter is invalid! Details:\nname={pkmn.name},'
                             f' which={which}, attr={current_attr}, '
                             f'counter={current_counter_val}')
        # Then decrement counter, and reset status/flag if counter is 0
        new_counter_val = current_counter_val - 1
        setattr(pkmn, counter_attr, new_counter_val)
        message = f'{pkmn.name} '
        if new_counter_val == 0:
            setattr(pkmn, attr_to_update, updated_val)
            if which == 'multiturn':
                pkmn.confused = True
                pkmn.confused_turns = globals.get_confusion_turns()
                post_message(f'{pkmn.name} became fatigued!')
            message += removed_condition_message
        else:
            message += condition_message
        if which not in ['trapping', 'multiturn']:
            post_message(message)

    def after_move(self, user, other):
        """
        Apply effects that occur after using a move:
        - Recurring damage (burn, poison/toxic, leech seed)
        """
        self.apply_recurring_damage(user, other)

    def apply_recurring_damage(self, user, other):
        """
        Apply recurring damage from burn, poison, leech seed
        """
        if user.status in ['BRN', 'PSN', 'TXC']:
            self.recurring_damage(user)
        if user.seeded:
            dmg = self.recurring_damage(user, seed=True)
            self.seed_heal(other, dmg)

    def recurring_damage(self, target, seed=False):
        damage = target.toxic_N*(target.max_hp//16)
        target.current_hp -= damage
        if seed:
            post_message(f'{target.name}\'s health was drained!')
        else:
            message = f'{target.name} was affected by its '
            if target.status == 'BRN':
                message += 'burn!'
            elif target.status in ['PSN', 'TXC']:
                message += 'poison!'
            else:
                raise ValueError('Called recurring_damage() on healthy Pokemon'
                                 f': name={target.name}'
                                 f', status={target.status}')
            post_message(message)
        if target.toxic and target.toxic_N < 15:
            target.toxic_N += 1
        return damage

    def seed_heal(self, target, amount):
        target.current_hp += amount
        post_message(f'{target.name} was healed!')

    def apply_move(self, move, user, other, first):
        """
        Main method for applying all moves
        """
        # Check if user hits itself in confusion
        hits_self = self.confusion_check(user, other)
        if hits_self:
            # Reset the multiturn status when hit in confusion
            if user.multiturn:
                while True:
                    try:
                        self.decrement_counter(user, 'multiturn')
                    except:
                        break
            # Don't do anything of the usual stuff for using this move
            return

        # decrement move's PP
        if move.name == 'Struggle':
            post_message(f'{user.name} is out of PP!')
        else:
            move.pp -= 1
            user.add_seen_move(move)
        post_message(f'{user.name} used {move.name}!')

        # damaging moves
        if move.category in ['Physical', 'Special']:
            self.apply_direct_damage(move, user, other)
        # status moves
        elif move.category == 'Status':
            self.apply_status(move, user, other)
        # stat changing moves
        elif move.category == 'Stat':
            self.apply_stat_changes(move, user, other)
        # unique moves with special effects
        else:
            pass

    def confusion_check(self, user, other):
        """
        Checks if user hits itself in confusion. If yes, applies damage.
        Returns bool hits_self.
        """
        hits_self = False
        if user.confused:
            hits_self = globals.rng_check(50)
            if hits_self:
                dmg = self.confusion_damage(user, other)
                user.current_hp -= dmg
                post_message(f'{user.name} hit itself in confusion!')
        return hits_self

    def confusion_damage(self, user, other):
        """
        Calculates damage user takes upon hitting itself in confusion. This
        attack is considered as a 40-base-power, typeless, physical move. It
        cannot score a critical hit. User's effective defense is doubled if
        the *opponent* has used Reflect. User's effective attack is halved if
        it is burned.
        Returns int damage.
        """
        a = user.attack
        d = user.defense
        """
        # Burn attack modifier should already be factored into user.attack
        if user.brn_flag:
            a = a//2
        """
        if other.reflect:
            d *= 2
            if d > 1024:
                d = d % 1024
        if a > 255 or d > 255:
            a = a//4
            d = d//4

        power = 40
        damage = int((2*user.level/5 + 2)*power*a/(d*50) + 2)
        # Apply random variation
        if damage == 1:
            rand_mult = 255
        else:
            rand_mult = random.randrange(217, 256)
        damage = damage * rand_mult // 255
        # Finally check if damage exceeds target's HP
        damage = min(damage, user.current_hp)
        return damage

    def apply_direct_damage(self, move, user, other):
        # accuracy check
        acc = self.get_effective_accuracy('Damage', move, user, other)
        move_hits = globals.gen1_rng_check(acc)
        if not move_hits:
            post_message('The move missed!')
            return
        # damage calculation
        damage = self.calc_damage(move, user, other)
        if damage != 0:
            post_message(f'{other.name} took {damage} damage!')
        other.current_hp -= damage
        # secondary status effects
        if move.status_accuracy:
            self.apply_status(move, user, other)
        # secondary stat changes
        if move.stat_accuracy:
            self.apply_stat_changes(move, user, other)

    def get_effective_accuracy(self, category, move, user, other):
        acc_mult = globals.get_stat_multiplier(user.stat_stages[5])
        eva_mult = globals.get_evasion_multiplier(other.stat_stages[6])
        if category == 'Damage':
            base = move.accuracy
            if base == '-':
                return base
            else:
                return base*acc_mult*eva_mult
        elif category == 'Stat':
            base = move.stat_accuracy
            if move.category == 'Stat':
                if base == '-':
                    return base
                else:
                    return base*acc_mult*eva_mult
            elif move.category in ['Physical', 'Special']:
                return base
            else:
                # weird combination
                raise ValueError(f'Unexpected combination category={category},'
                                 f' move.category={move.category}')
        elif category == 'Status':
            base = move.status_accuracy
            if move.category == 'Status':
                if base == '-':
                    return base
                else:
                    return base*acc_mult*eva_mult
            elif move.category in ['Physical', 'Special']:
                return base
            else:
                # weird combination
                raise ValueError(f'Unexpected combination category={category},'
                                 f' move.category={move.category}')
        else:
            raise ValueError(f'Unexpected category {category}')

    def calc_damage(self, move, user, target):
        # return 10   # for testing

        # First check for a critical hit, because this affects stat values
        crit = random.randrange(256) < self.crit_rng_threshold(user, move)
        crit_mult = 2 if crit else 1
        if crit:
            post_message('Critical hit!')
        # Determine effective att/def stats
        if move.category == 'Physical':
            if crit:
                a = user.calc_stat(1, True)
                d = target.calc_stat(2, True)
            else:
                a = user.attack
                d = target.defense
        else:
            if crit:
                a = user.calc_stat(4, True)
                d = target.calc_stat(4, True)
            else:
                a = user.special
                d = target.special
        if a > 255 or d > 255:
            a = a//4
            d = d//4

        raw_power = move.base_power
        if raw_power == '-':
            return self.get_fixed_damage(move, user, target)
        else:
            power = raw_power
        base_damage = int((2*user.level*crit_mult/5 + 2)*power*a/(d*50) + 2)
        # Apply type-dependent multipliers
        stab = 1
        if move.type in [user.type1, user.type2]:
            stab = 1.5
        type1 = globals.get_type_mult(move.type, target.type1)
        type2 = globals.get_type_mult(move.type, target.type2)
        if (type1*type2) > 1:
            post_message('It\'s super effective!')
        if (type1*type2) > 0 and (type1*type2) < 1:
            post_message('It\'s not very effective...')
        if (type1*type2) == 0:
            post_message('It has no effect...')
        damage = int(base_damage*stab)
        damage = int(damage*type1)
        damage = int(damage*type2)
        # Apply random variation
        if damage == 1:
            rand_mult = 255
        else:
            rand_mult = random.randrange(217, 256)
        damage = damage * rand_mult // 255
        # Finally check if damage exceeds target's HP
        damage = min(damage, target.current_hp)
        return damage

    def crit_rng_threshold(self, user, move):
        spe = user.base_spe
        thresh = spe//2
        if move.high_crit:
            thresh = min(move.high_crit*thresh, 255)
        return thresh

    def get_fixed_damage(self, move, user, target):
        return min(10, target.current_hp)   # for testing

    def apply_status(self, move, user, other):
        target = other if move.status_target == 'other' else user
        # Pokemon cannot be status'd by the secondary effect of a damaging
        # move of their own type
        if (move.category in ['Physical', 'Special'] and
                move.type in [target.type1, target.type2]):
            return
        # Ground Pokemon can't be paralyzed by Electric moves
        if (move.type == 'Electric' and
                'Ground' in [target.type1, target.type2]):
            return
        # don't apply a new status if the target already has one, except Rest
        if target.status:
            self.attempt_status_overwrite(move, target)
        else:
            # target doesn't already have a status, so proceed normally
            # accuracy check
            acc = self.get_effective_accuracy('Status', move, user, other)
            move_hits = globals.rng_check(acc)
            if move_hits:
                target.status = move.status
                message = f'{target.name} '
                if move.status == 'PRZ':
                    message += 'became paralyzed!'
                    target.prz_flag = True
                    target.recalc_stats()
                if move.status == 'BRN':
                    message += 'was burned!'
                    target.brn_flag = True
                    target.recalc_stats()
                if move.status == 'FRZ':
                    message += 'was frozen solid!'
                if move.status == 'SLP':
                    if move.name == 'Rest':
                        message += 'fell asleep and became healthy!'
                        target.current_hp = target.max_hp
                        target.sleep_turns = 2
                    else:
                        message += 'fell asleep!'
                        target.sleep_turns = globals.sleep_turns()
                if move.status == 'PSN':
                    message += 'was poisoned!'
                if move.status == 'TXC':
                    message += 'was badly poisoned!'
                post_message(message)
            else:
                if move.category == 'Status':
                    post_message('The move missed!')

    def attempt_status_overwrite(self, move, target):
        # if status is a side effect, do nothing
        if move.category != 'Status':
            return
        # otherwise, print a move failure message
        else:
            # the exception is the move Rest, which overwrites status
            if move.name != 'Rest':
                message = f'{target.name} is already '
                if target.status == 'PRZ':
                    message += 'paralyzed!'
                if target.status == 'BRN':
                    message += 'burned!'
                if target.status == 'FRZ':
                    message += 'frozen!'
                if target.status == 'SLP':
                    message += 'asleep!'
                if target.status == 'PSN':
                    message += 'poisoned!'
            else:
                # Rest special case
                target.status = 'SLP'
                target.sleep_turns = 2
                target.current_hp = target.max_hp
                message = f'{target.name} fell asleep and became healthy!'
            post_message(message)
            return

    def apply_stat_changes(self, move, user, other):
        # accuracy check
        acc = self.get_effective_accuracy('Stat', move, user, other)
        move_hits = globals.rng_check(acc)
        if move_hits:
            target = other if move.stat_target == 'other' else user
            message = f'{target.name}\'s '
            message += globals.index_to_stat[move.stat_index] + ' '
            current_stage = target.stat_stages[move.stat_index]
            if ((current_stage == -6 and move.stat_delta < 0)
                    or (current_stage == -5 and move.stat_delta < -1)):
                message += 'could not be lowered any more!'
            elif ((current_stage == 6 and move.stat_delta > 0)
                  or (current_stage == 5 and move.stat_delta > 1)):
                message += 'could not be raised any more!'
            else:
                target.stat_stages[move.stat_index] += move.stat_delta
                target.recalc_stats()
                sharply = 'sharply ' if abs(move.stat_delta) >= 2 else ''
                message += sharply
                message += ('increased!' if move.stat_delta > 0
                            else 'decreased!')
            post_message(message)
        else:
            if move.category == 'Stat':
                post_message('The move missed!')
