import globals
from move import Move
from trainer import Trainer
from ai import AI
from moveuser import MoveUser
from ui import post_message


class Battle:
    """
    """

    def __init__(self, ui='text', trainer1_ai='human', trainer2_ai='random'):
        globals.UI = ui
        self.trainer1 = Trainer('Player')
        self.trainer2 = Trainer('CPU')
        self.trainer1.print()
        # self.trainer2.print()
        self.ai1 = AI(trainer1_ai, trainer=self.trainer1, other=self.trainer2)
        self.ai2 = AI(trainer2_ai, trainer=self.trainer2, other=self.trainer1)
        self.mu = MoveUser()

    @property
    def is_over(self):
        return (self.trainer1.all_fainted() or self.trainer2.all_fainted())

    def round(self):
        post_message('\nCurrent battle status:', wait=False)
        self.trainer1.print_active()
        self.trainer2.print_active(seen_moves=True)
        post_message()
        action1 = self.ai1.get_action()
        action2 = self.ai2.get_action()
        self.validate_action(action1, self.trainer1)
        self.validate_action(action2, self.trainer2)
        first = self.get_priority(action1, action2)
        apply_end_round, l_pkmn = self.apply_actions(first, action1, action2)
        if apply_end_round:
            self.end_round(l_pkmn)

    def turn(self, trainer, action, first=False):
        """
        Applies this trainer's action.
        Returns (apply_end_round, pkmn_included_in_end_round) -- specifically,
        if this Pokemon moved, pkmn_included_in_end_round = trainer.active
        """
        apply_end_round = True
        return_pkmn = False
        if trainer == self.trainer1:
            other_trainer = self.trainer2
        else:
            other_trainer = self.trainer1

        if action[0] == 'swap':
            self.swap(trainer, action[1])
        elif action[0] == 'move':
            if action[1] == 4:
                move = Move('Struggle')
            else:
                move = trainer.active.moves[action[1]]
            can_use_move = self.mu.before_move(trainer.active)
            if can_use_move:
                self.mu.apply_move(move, trainer.active,
                                   other_trainer.active, first)
                caused_faint = self.check_for_faints(trainer.active,
                                                     other_trainer.active)
                if caused_faint:
                    apply_end_round = False
                else:
                    self.mu.after_move(trainer.active, other_trainer.active)
            else:
                return_pkmn = True
        else:
            raise ValueError(f'Invalid action type {action[0]}')

        pkmn_l = [trainer.active] if return_pkmn else []
        return apply_end_round, pkmn_l

    def check_for_faints(self, user, defender):
        something_fainted = False
        if user == self.trainer1.active:
            user_trainer, defender_trainer = self.trainer1, self.trainer2
            user_ai, defender_ai = self.ai1, self.ai2
        else:
            user_trainer, defender_trainer = self.trainer2, self.trainer1
            user_ai, defender_ai = self.ai2, self.ai1
        if defender.is_fainted():
            something_fainted = True
            post_message(f'{defender.name} fainted!')
            if not defender_trainer.all_fainted():
                swap_action = defender_ai.get_swap()
                self.swap(defender_trainer, swap_action[1])
        # Also need to check if user fainted due to recoil/Selfdestruct
        if user.is_fainted():
            something_fainted = True
            post_message(f'{user.name} fainted!')
            if not user_trainer.all_fainted():
                swap_action = user_ai.get_swap()
                self.swap(user_trainer, swap_action[1])
        return something_fainted

    def apply_actions(self, first, action1, action2):
        first_trainer = self.trainer1 if first == 1 else self.trainer2
        second_trainer = self.trainer2 if first == 1 else self.trainer1
        first_action = action1 if first == 1 else action2
        second_action = action2 if first == 1 else action1

        # apply first action
        apply_end_round1, pkmn_l1 = self.turn(first_trainer, first_action,
                                              first=True)
        # if first action didn't cause a faint, apply second action
        apply_end_round2 = False
        pkmn_l2 = []
        if apply_end_round1:
            apply_end_round2, pkmn_l2 = self.turn(second_trainer,
                                                  second_action, first=False)

        return (apply_end_round1 and apply_end_round2), (pkmn_l1 + pkmn_l2)

    def swap(self, trainer, index):
        try:
            trainer.active = index
            post_message(f'{trainer.name} sent out '
                         f'{trainer.active.name}!')
        except IndexError:
            print(f'Error: index {index} is out of range.')

    def get_priority(self, action1, action2):
        if (action1[0] == 'swap' and action2[0] == 'move'):
            first = 1
        elif (action1[0] == 'move' and action2[0] == 'swap'):
            first = 2
        else:
            if (self.trainer1.active.speed > self.trainer2.active.speed):
                first = 1
            elif (self.trainer1.active.speed < self.trainer2.active.speed):
                first = 2
            else:
                first = 1 if globals.rng_check(50) else 2
        return first

    def end_round(self, l_pkmn):
        """
        Apply any Poison/Burn/Leech Seed damage that was skipped by a Pokemon
        missing its turn.
        """
        for pkmn in l_pkmn:
            affected = (self.trainer1.active if pkmn == self.trainer1.active
                        else self.trainer2.active)
            other = (self.trainer2.active if pkmn == self.trainer1.active
                     else self.trainer1.active)
            self.mu.apply_recurring_damage(affected, other)

    def validate_action(self, action, trainer):
        if action[0] == 'swap':
            if action[1] < 0 or action[1] >= len(trainer.party_alive):
                raise IndexError(f'Invalid party index {action[1]}')
        elif action[0] == 'move':
            if action[1] != 4:
                if action[1] < 0 or action[1] >= len(trainer.active.moves):
                    raise IndexError(f'Invalid move index {action[1]}')
                if trainer.active.moves[action[1]].pp <= 0:
                    raise ValueError(
                        f'Selected move (index={action[1]}) has no PP')
        else:
            raise ValueError(f'Invalid action type {action[0]}')
