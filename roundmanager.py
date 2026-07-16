import globals
from mediator import Colleague
from move import Move
from moveuser import MoveUser
from turnmanager import TurnManager
from ui import post_message


class RoundManager(Colleague):
    """
    Main class for advancing the battle one round at a time.
    """

    def __init__(self, trainer1, trainer2):
        super().__init__()
        self.trainer1 = trainer1
        self.trainer2 = trainer2
        self.mu = MoveUser()
        self.tm = TurnManager(self.mu)
        self._proceed = True
        self._apply_end_round = True
        self._end_round_pkmn = []

    def round(self):
        """
        Main function for advancing the battle by one round.
        """

        self._proceed = True
        self.print()
        self.trainer1.update_action()
        self.trainer2.update_action()
        first_trainer, second_trainer = self.get_turn_order()
        self.turn(first_trainer, first=True)
        if not self._proceed:
            return
        self.turn(second_trainer, first=False)
        if self._proceed:
            self.end_round()

    def turn(self, trainer, first=False):
        """
        Main function for applying one trainer's action during their turn.
        """

        self._proceed = True
        other_trainer = self._get_other_trainer(trainer)
        action = trainer.next_action
        if action[0] == 'swap':
            trainer.swap(action[1])
        elif action[0] == 'move':
            move = self._get_move(trainer.active, action[1])
            bmd = self.tm.before_move(trainer.active, other_trainer.active)
            if not bmd['can_move']:
                self._end_round_pkmn.append(trainer.active)
                return
            self.mu.apply_move(move, trainer.active,
                               other_trainer.active, first)
            if self._proceed:
                self.tm.after_move(trainer.active, other_trainer.active)
        else:
            raise ValueError(f'Invalid action type {action[0]}')

    def end_round(self):
        """
        Apply any Poison/Burn/Leech Seed damage that was skipped by a Pokemon
        missing its turn.
        """
        for pkmn in self._end_round_pkmn:
            affected = pkmn
            other = (self.trainer2.active if pkmn == self.trainer1.active
                     else self.trainer1.active)
            self.tm.apply_all_recurring_damage(affected, other)
        self._end_round_pkmn = []

    def receive_event(self, event_d):
        if event_d['event_type'] == 'faint':
            self._proceed = False
        else:
            pass

    def print(self):
        if globals.UI == 'text':
            post_message('Current battle status:', wait=True)
        stats = True if globals.DEBUG else False
        self.trainer1.print_active(stats=stats)
        self.trainer2.print_active(stats=stats, seen_moves=True)
        post_message('', end='')

    def get_turn_order(self):
        """
        Determines order of turns based on each trainer's chosen action.
        Returns first_trainer, second_trainer.
        """
        a1 = self.trainer1.next_action
        a2 = self.trainer2.next_action
        if (a1[0] == 'swap' and a2[0] == 'move'):
            first, second = self.trainer1, self.trainer2
        elif (a1[0] == 'move' and a2[0] == 'swap'):
            first, second = self.trainer2, self.trainer1
        else:
            first, second = self._get_priority_order(a1, a2)
        return first, second

    def _get_priority_order(self, a1, a2):
        """
        Determines which Pokemon moves first when both are using moves, based
        on move priority.
        Returns first_trainer, second_trainer.
        """
        m1 = self.trainer1.active.moves[a1[1]]
        m2 = self.trainer2.active.moves[a2[1]]
        p1, p2 = m1.priority, m2.priority
        if p1 > p2:
            first, second = self.trainer1, self.trainer2
        elif p1 < p2:
            first, second = self.trainer2, self.trainer1
        else:
            first, second = self._get_move_order()
        return first, second

    def _get_move_order(self):
        """
        Determines which Pokemon moves first when both are using moves of equal
        priority.
        Returns first_trainer, second_trainer.
        """
        if (self.trainer1.active.speed > self.trainer2.active.speed):
            first, second = self.trainer1, self.trainer2
        elif (self.trainer1.active.speed < self.trainer2.active.speed):
            first, second = self.trainer2, self.trainer1
        else:
            # Speed tie -- decide by a coin flip
            if globals.rng_check(50):
                first, second = self.trainer1, self.trainer2
            else:
                first, second = self.trainer2, self.trainer1
        return first, second

    def _get_other_trainer(self, trainer):
        return self.trainer2 if trainer == self.trainer1 else self.trainer1

    def _get_move(self, pkmn, index):
        if index == 4:
            move = Move('Struggle')
        else:
            move = pkmn.moves[index]
        return move
