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
        self.trap_damage = 0

    def apply_move(self, move, user, other, first):
        """
        Main method for applying all moves
        """
        '''
        # Check if user hits itself in confusion
        hits_self = self.confusion_check(user, other)
        if hits_self:
            # Reset the multiturn status when hit in confusion
            if user.sm.get_counter('multiturn'):
                user.sm.reset_counter('multiturn')
            # Don't do anything of the usual stuff for using this move
            return
        '''

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
        # Need to implement
        return min(10, target.current_hp)   # for testing

    def proc_status(self, move, target):
        target.sm.status = move.status
        message = f'{target.name} '
        if move.status == 'PRZ':
            message += 'became paralyzed!'
            # target.prz_flag = True
            # target.recalc_stats()
            target.apply_status_debuff()
        elif move.status == 'BRN':
            message += 'was burned!'
            # target.brn_flag = True
            # target.recalc_stats()
            target.apply_status_debuff()
        elif move.status == 'FRZ':
            message += 'was frozen solid!'
        elif move.status == 'SLP':
            if move.name == 'Rest':
                message += 'fell asleep and became healthy!'
                target.current_hp = target.max_hp
                turns = 2
            else:
                message += 'fell asleep!'
                turns = globals.sleep_turns()
            target.sm.turn_on_counter('sleep', turns)
        elif move.status == 'PSN':
            message += 'was poisoned!'
        elif move.status == 'TXC':
            message += 'was badly poisoned!'
            target.sm.turn_on_counter('toxic', 1)
        else:
            raise ValueError(f'Move {move.name} with invalid status '
                             f'{move.status}')
        return message

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
        # and unfreezing when hit by a fire move capable of causing BRN
        if target.sm.status:
            self.attempt_status_overwrite(move, target)
        else:
            # target doesn't already have a status, so proceed normally
            # accuracy check
            acc = self.get_effective_accuracy('Status', move, user, other)
            move_hits = globals.rng_check(acc)
            if move_hits:
                message = self.proc_status(move, target)
                post_message(message)
            else:
                if move.category == 'Status':
                    post_message('The move missed!')

    def attempt_status_overwrite(self, move, target):
        # if status is a side effect, check for unfreezing
        if move.category != 'Status':
            if target.sm.status == 'FRZ' and move.status == 'BRN':
                target.sm.status = None
                post_message(f'{target.name} was thawed!')
        # otherwise, print a move failure message
        else:
            # the exception is the move Rest, which overwrites status
            if move.name != 'Rest':
                message = f'{target.name} is already '
                if target.sm.status == 'PRZ':
                    message += 'paralyzed!'
                if target.sm.status == 'BRN':
                    message += 'burned!'
                if target.sm.status == 'FRZ':
                    message += 'frozen!'
                if target.sm.status == 'SLP':
                    message += 'asleep!'
                if target.sm.status in ['PSN', 'TXC']:
                    message += 'poisoned!'
            else:
                # Rest special case
                if target.current_hp < target.max_hp:
                    message = self.proc_status(move, target)
                else:
                    message = 'The move failed!'
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
                # Stage is ok. Check whether updated stat would leave the
                # allowed [1, 999] range. Note, this does not apply to
                # Accuracy and Evasion
                target.stat_stages[move.stat_index] += move.stat_delta
                if move.stat_index in range(1, 5):
                    # Attack, Defense, Speed or Special change
                    new_val = target.calc_stat(move.stat_index)
                    if new_val < 1:
                        message += 'could not be lowered any more!'
                        # Undo the stage change
                        target.stat_stages[move.stat_index] = current_stage
                    elif new_val > 999:
                        message += 'could not be raised any more!'
                        # Undo the stage change
                        target.stat_stages[move.stat_index] = current_stage
                    else:
                        # Change is successful
                        """
                        # Don't recalculate all stats -- only the relevant one
                        target.recalc_stats()
                        """
                        target.stats[move.stat_index - 1] = new_val
                        sharply = ('sharply ' if abs(move.stat_delta) >= 2
                                   else '')
                        message += sharply
                        message += ('increased!' if move.stat_delta > 0
                                    else 'decreased!')
                        # Reapply prz/brn debuff to other, if applicable
                        other.apply_status_debuff()
                else:
                    # Accuracy or Evasion change
                    sharply = 'sharply ' if abs(move.stat_delta) >= 2 else ''
                    message += sharply
                    message += ('increased!' if move.stat_delta > 0
                                else 'decreased!')
                    # Reapply prz/brn debuff to other, if applicable
                    other.apply_status_debuff()
            post_message(message)

        else:
            if move.category == 'Stat':
                post_message('The move missed!')
