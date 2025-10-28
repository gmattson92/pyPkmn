import globals
from move import Move
from trainer import Trainer
from ai import AI
import random


class Battle:
    """
    """

    def __init__(self, ui='text', trainer1_ai='human', trainer2_ai='random'):
        globals.UI = ui
        self.trainer1 = Trainer('Player')
        self.trainer1.print()
        self.trainer2 = Trainer('CPU')
        self.trainer2.print()
        self.ai1 = AI(trainer1_ai, trainer=self.trainer1, other=self.trainer2)
        self.ai2 = AI(trainer2_ai, trainer=self.trainer2, other=self.trainer1)

    @property
    def is_over(self):
        return (self.trainer1.all_fainted() or self.trainer2.all_fainted())

    def turn(self):
        self.trainer1.print_active()
        self.trainer2.print_active()
        action1 = self.ai1.get_action()
        action2 = self.ai2.get_action()
        self.validate_action(action1, self.trainer1)
        self.validate_action(action2, self.trainer2)
        first = self.get_priority(action1, action2)
        apply_end_turn = self.apply_actions(first, action1, action2)
        if apply_end_turn:
            self.end_turn()

    def check_for_faints(self, user, defender):
        something_fainted = False
        user_trainer, defender_trainer = self.trainer1, self.trainer2
        user_ai, defender_ai = self.ai1, self.ai2
        if user == self.trainer2.active:
            user_trainer, defender_trainer = self.trainer2, self.trainer1
            user_ai, defender_ai = self.ai2, self.ai1
        if defender.is_fainted():
            something_fainted = True
            print(f'{defender.name} fainted!')
            if not defender_trainer.all_fainted():
                swap_action = defender_ai.get_swap()
                self.swap(defender_trainer, swap_action[1])
        # Also need to check if user fainted due to recoil/Selfdestruct
        if user.is_fainted():
            something_fainted = True
            print(f'{user.name} fainted!')
            if not user_trainer.all_fainted():
                swap_action = user_ai.get_swap()
                self.swap(user_trainer, swap_action[1])
        return something_fainted

    def apply_actions(self, first, action1, action2):
        apply_end_turn = True
        first_trainer = self.trainer1 if first == 1 else self.trainer2
        second_trainer = self.trainer2 if first == 1 else self.trainer1
        first_action = action1 if first == 1 else action2
        second_action = action2 if first == 1 else action1

        # apply first action
        if first_action[0] == 'swap':
            self.swap(first_trainer, first_action[1])
        if first_action[0] == 'move':
            if first_action[1] == -1:
                first_move = Move('Struggle')
            else:
                first_move = first_trainer.active.moves[first_action[1]]
            self.apply_move(first_move,
                            first_trainer.active,
                            second_trainer.active)
            caused_faint = self.check_for_faints(first_trainer.active,
                                                 second_trainer.active)
            if caused_faint:
                apply_end_turn = False
                return apply_end_turn

        # apply second action
        if second_action[0] == 'swap':
            self.swap(second_trainer, second_action[1])
        if second_action[0] == 'move':
            if second_action[1] == -1:
                second_move = Move('Struggle')
            else:
                second_move = second_trainer.active.moves[second_action[1]]
            self.apply_move(second_move,
                            second_trainer.active,
                            first_trainer.active)
            caused_faint = self.check_for_faints(second_trainer.active,
                                                 first_trainer.active)
            if caused_faint:
                apply_end_turn = False
                return apply_end_turn

        # if nothing fainted
        return apply_end_turn

    def user_can_move(self, user):
        if user.status == 'SLP':
            print(f'{user.name} is asleep!')
            return False
        elif user.status == 'FRZ':
            print(f'{user.name} is frozen solid!')
            return False
        elif user.status == 'PRZ':
            fully_prz = globals.rng_check(globals.FULL_PRZ_CHANCE)
            if fully_prz:
                print(f'{user.name} is fully paralyzed!')
                return False
            else:
                return True
        else:
            return True

    def apply_direct_damage(self, move, user, other):
        # accuracy check
        acc = self.get_effective_accuracy('Damage', move, user, other)
        move_hits = globals.rng_check(acc)
        if not move_hits:
            print('The move missed!')
            return
        # damage calculation
        damage = self.calc_damage(move, user, other)
        if damage != 0:
            print(f'{other.name} took {damage} damage!')
        other.current_hp -= damage
        # secondary status effects
        if move.status_accuracy:
            self.apply_status(move, user, other)
        # secondary stat changes
        if move.stat_accuracy:
            self.apply_stat_changes(move, user, other)

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
            print(message)
            return

    def apply_status(self, move, user, other):
        target = other if move.status_target == 'other' else user
        # Pokemon cannot be status'd by the secondary effect of a damaging
        # move of their own type
        if (move.category in ['Physical', 'Special'] and
                move.type in [target.type1, target.type2]):
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
                print(message)
            else:
                if move.category == 'Status':
                    print('The move missed!')

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
            print(message)
        else:
            if move.category == 'Stat':
                print('The move missed!')

    def apply_move(self, move, user, other):
        can_use = self.user_can_move(user)
        if not can_use:
            return

        # logic for confusion status
        # ...

        # decrement move's PP
        if move.name == 'Struggle':
            print(f'{user.name} is out of PP!')
        else:
            move.pp -= 1
        print(f'{user.name} used {move.name}.')

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

    def get_effective_accuracy(self, category, move, user, other):
        acc_mult = globals.get_stat_multiplier(user.stat_stages[5])
        eva_mult = globals.get_evasion_multiplier(other.stat_stages[6])
        if category == 'Damage':
            base = move.accuracy
            return base*acc_mult*eva_mult
        elif category == 'Stat':
            if move.category == 'Stat':
                base = move.stat_accuracy
                return base*acc_mult*eva_mult
            elif move.category in ['Physical', 'Special']:
                return move.stat_accuracy
            else:
                # weird combination
                raise ValueError(f'Unexpected combination category={category},'
                                 f' move.category={move.category}')
        elif category == 'Status':
            if move.category == 'Status':
                base = move.status_accuracy
                return base*acc_mult*eva_mult
            elif move.category in ['Physical', 'Special']:
                return move.status_accuracy
            else:
                # weird combination
                raise ValueError(f'Unexpected combination category={category},'
                                 f' move.category={move.category}')
        else:
            raise ValueError(f'Unexpected category {category}')

    def swap(self, trainer, index):
        try:
            trainer.active = trainer.party_alive[index]
            print(f'{trainer.name} sent out '
                  f'{trainer.active.name}!')
        except IndexError:
            print(f'Error: index {index} is out of range.')

    def get_priority(self, action1, action2):
        if (action1[0] == 'swap' and action2[0] == 'move'):
            return 1
        elif (action1[0] == 'move' and action2[0] == 'swap'):
            return 2
        else:
            if (self.trainer1.active.speed > self.trainer2.active.speed):
                return 1
            elif (self.trainer1.active.speed < self.trainer2.active.speed):
                return 2
            else:
                return 1 if globals.rng_check(50) else 2

    def end_turn(self):
        """
        Apply any Poison/Burn/Leech Seed damage and decrement status counters
        """
        pass

    def crit_rng_threshold(self, user, move):
        spe = user.base_spe
        thresh = spe//2
        if move.name in ['Crabhammer', 'Karate Chop', 'Razor Leaf', 'Slash']:
            thresh = min(8*thresh, 255)
        return thresh

    def calc_damage(self, move, user, target):
        # return 10   # for testing

        # First check for a critical hit, because this affects stat values
        crit = random.randrange(256) < self.crit_rng_threshold(user, move)
        crit_mult = 2 if crit else 1
        if crit:
            print('Critical hit!')
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

        power = move.base_power
        base_damage = int((2*user.level*crit_mult/5 + 2)*power*a/(d*50) + 2)
        # Apply type-dependent multipliers
        stab = 1
        if move.type in [user.type1, user.type2]:
            stab = 1.5
        type1 = globals.get_type_mult(move.type, target.type1)
        type2 = globals.get_type_mult(move.type, target.type2)
        if (type1*type2) > 1:
            print('It\'s super effective!')
        if (type1*type2) > 0 and (type1*type2) < 1:
            print('It\'s not very effective...')
        if (type1*type2) == 0:
            print('It has no effect...')
        damage = int(base_damage*stab)
        damage = int(damage*type1)
        damage = int(damage*type2)
        # Apply random variation
        if damage == 1:
            rand_mult = 255
        else:
            rand_mult = random.randrange(217, 256)
        damage = damage * rand_mult // 255
        return damage

    def validate_action(self, action, trainer):
        if action[0] == 'swap':
            if action[1] < 0 or action[1] >= len(trainer.party_alive):
                raise IndexError(f'Invalid party index {action[1]}')
        elif action[0] == 'move':
            if action[1] < -1 or action[1] >= len(trainer.active.moves):
                raise IndexError(f'Invalid move index {action[1]}')
            if action[1] > -1 and trainer.active.moves[action[1]].pp <= 0:
                raise ValueError(
                    f'Selected move (index={action[1]}) has no PP')
        else:
            raise ValueError(f'Invalid action type {action[0]}')
