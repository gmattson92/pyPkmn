import globals
from trainer import Trainer
from ai import AI


class Battle:
    """
    """

    def __init__(self, ui='text', trainer1_ai='human', trainer2_ai='random'):
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
            self.apply_move(first_trainer.active.moves[first_action[1]],
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
            self.apply_move(second_trainer.active.moves[second_action[1]],
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
        move_hits = globals.rng_check(move.accuracy)
        if not move_hits:
            print('The move missed!')
            return
        # damage calculation
        damage = self.calc_damage(move, user, other)
        effective_damage = min(damage, other.current_hp)
        print(f'{other.name} took {effective_damage} damage!')
        other.current_hp -= effective_damage
        # secondary status effects
        if move.status_accuracy:
            self.apply_status(move, user, other)
        # secondary stat changes
        if move.stat_accuracy:
            self.apply_stat_changes(move, user, other)

    def overwite_status(self, move, target):
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
        if target.status:
            # don't apply a new status if the target already has one
            self.overwite_status(move, target)
        else:
            # target doesn't already have a status, so proceed normally
            # accuracy check
            move_hits = globals.rng_check(move.status_accuracy)
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
        move_hits = globals.rng_check(move.stat_accuracy)
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

    def calc_damage(self, move, user, target):
        return 10   # for testing
        """
        a = user.attack if move.category == 'Physical' else user.special
        d = other.defense if move.category == 'Physical' else other.special
        pow = move.base_power
        """

    def validate_action(self, action, trainer):
        if action[0] == 'swap':
            if action[1] < 0 or action[1] >= len(trainer.party_alive):
                raise IndexError(f'Invalid party index {action[1]}')
        elif action[0] == 'move':
            if action[1] < 0 or action[1] >= len(trainer.active.moves):
                raise IndexError(f'Invalid move index {action[1]}')
            if trainer.active.moves[action[1]].pp <= 0:
                raise ValueError(
                    f'Selected move (index={action[1]}) has no PP')
        else:
            raise ValueError(f'Invalid action type {action[0]}')
