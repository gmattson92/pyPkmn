import globals
from ui import post_message
import random


class TurnManager:
    """
    Handles all details of a Pokemon taking its turn -- i.e. determining:
        - whether it can use a move
        - what move it uses (if move selection was disabled this round)
        - whether it should take any recurring damage, and applying that damage
            at the appropriate time
        - what changes need to be made to various status flags and counters,
            and applying those changes
    Most changes to status counters are applied in before_move(). The exception
    is trapping/binding, which changes in RoundManager.end_round().
    """

    def __init__(self, mu):
        self.mu = mu
        self._counter_last_damage = 0
        self._trap_damage = 0

    @property
    def counter_last_damage(self):
        return self._counter_last_damage

    @counter_last_damage.setter
    def counter_last_damage(self, val):
        self._counter_last_damage = val

    @property
    def trap_damage(self):
        return self._trap_damage

    @trap_damage.setter
    def trap_damage(self, val):
        self._trap_damage = val

    def before_move(self, user, other):
        """
        Determines whether a Pokemon can use its chosen move this turn, and
        applies certain changes to Pokemon's status --
            - decrementing the Sleep counter & checking for expiration
            - checking for full paralysis
            - resetting flinch and Hyper Beam recharge flags
            - decrementing the Confusion counter & checking for expiration
            - decrementing the Disable counter & checking for expiration
            - checking if Pokemon hits itself in confusion
            - decrementing the Multiturn counter & checking for expiration,
                or resetting if Pokemon hit itself in confusion
        Note that the Trapping/Trapped counters decrement during end_round,
        rather than here like all the other counters; likewise for the Toxic
        counter incrementing. However, Trap counters can be reset here
        depending on other status effects.

        Returns dict with overall can/can't move determination and details on
        which checks pass and fail. Valid keys are:
            - 'can_move'
            - 'fully_przd'
            - 'asleep_frozen'
            - 'flinched'
            - 'recharging'
            - 'trap_active'
            - 'hit_self'
        """
        bm_dict = {}
        update_fns = [self.update_major_status,
                      self.update_flinch,
                      self.update_recharge,
                      self.update_trap_active,
                      self.update_disable,
                      self.update_confusion]
        for fn in update_fns:
            fn(user, bm_dict)

        # Overall can/can't move
        can_move = self.can_move(bm_dict)
        bm_dict['can_move'] = can_move

        # Check for pkmn hitting itself in confusion (but skip this if pkmn
        # can't move for another reason)
        hit_self = False
        if can_move:
            hit_self = self.confusion_check(user, other)
        bm_dict['hit_self'] = hit_self

        self.update_multiturn(user, bm_dict)

        return bm_dict

    def after_move(self, user, other):
        """
        Apply effects that occur after using a move:
            - Recurring damage (burn, poison/toxic, leech seed)
        """
        self.apply_all_recurring_damage(user, other)

    def update_fully_przd(self, pkmn, bm_dict):
        """
        Checks if pkmn is fully paralyzed and prevented from moving this turn.
        If so, posts message. Updates bm_dict with Boolean result.
        """
        fully_przd = False
        if pkmn.sm.status == 'PRZ':
            fully_przd = globals.rng_check(globals.FULL_PRZ_CHANCE)
            if fully_przd:
                post_message(f'{pkmn.name} is fully paralyzed!')
        bm_dict['fully_przd'] = fully_przd

    def update_major_status(self, pkmn, bm_dict):
        """
        Checks if pkmn is prevented from moving by a non-volatile status
        condition and, if so, posts the appropriate message. Also handles
        decrementing the sleep counter. Updates bm_dict with bools for full
        paralysis, and asleep/frozen.
        """
        self.update_fully_przd(pkmn, bm_dict)
        asleep_frozen = False
        if pkmn.sm.status == 'SLP':
            asleep_frozen = True
            message = pkmn.sm.decrement_counter('sleep')
            post_message(message)
        if pkmn.sm.status == 'FRZ':
            asleep_frozen = True
            post_message(f'{pkmn.name} is frozen solid!')
        bm_dict['asleep_frozen'] = asleep_frozen

    def update_flinch(self, pkmn, bm_dict):
        if pkmn.sm.get_flag('flinch'):
            flinched = True
            post_message(f'{pkmn.name} flinched!')
            # Reset the flinch flag
            pkmn.sm.reset_flag('flinch')
        else:
            flinched = False
        bm_dict['flinched'] = flinched

    def update_recharge(self, pkmn, bm_dict):
        if pkmn.sm.get_flag('recharge'):
            recharging = True
            post_message(f'{pkmn.name} has to recharge!')
            # Reset the recharge flag, unless pkmn is frozen
            if pkmn.sm.status != 'FRZ':
                pkmn.sm.reset_flag('recharge')
        else:
            recharging = False
        bm_dict['recharging'] = recharging

    def update_trap_active(self, pkmn, bm_dict):
        if pkmn.sm.get_counter('trapped') or pkmn.sm.get_counter('trapping'):
            trap_active = True
        else:
            trap_active = False
        bm_dict['trap_active'] = trap_active

    def can_move(self, bm_dict):
        """
        Checks whether pkmn can move this turn, or is prevented from moving by
        a major status, flinch, or recharge. Note that trapped/trapping status
        are **not** included for this purpose, and are handled separately.
        Returns bool.
        """
        can_move = True
        # Major status
        if bm_dict['fully_przd'] or bm_dict['asleep_frozen']:
            can_move = False
        # Non-status
        if bm_dict['flinched'] or bm_dict['recharging']:
            can_move = False
        return can_move

    def decrement_cnf_dsb(self, bm_dict):
        """
        Checks whether to decrement the Confusion and Disable counters, which
        are paused during sleep, freeze, flinches and recharge turns, but do
        decrement during full paralysis and trapping turns. Returns bool.
        """
        decrement = ((not bm_dict['asleep_frozen'])
                     and (not bm_dict['flinched'])
                     and (not bm_dict['recharging']))
        return decrement

    def update_disable(self, pkmn, bm_dict):
        if self.decrement_cnf_dsb(bm_dict):
            if pkmn.sm.get_counter('disable'):
                msg = pkmn.sm.decrement_counter('disable')
                post_message(msg)

    def update_confusion(self, pkmn, bm_dict):
        if self.decrement_cnf_dsb(bm_dict):
            if pkmn.sm.get_counter('confusion'):
                msg = pkmn.sm.decrement_counter('confusion')
                post_message(msg)

    def confusion_check(self, user, other):
        """
        Checks if user hits itself in confusion. If yes, applies damage.
        Returns bool hits_self.
        """
        hits_self = False
        if user.sm.get_counter('confusion'):
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
        if other.sm.get_flag('reflect'):
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

    def update_multiturn(self, pkmn, bm_dict):
        """
        Multiturn, which is more complicated -- hits in confusion and full
        paralysis reset the move completely; sleep, freeze and trapped all
        pause the move but do not decrement the counter.
        """
        if pkmn.sm.get_counter('multiturn'):
            reset_mlt = bm_dict['fully_przd'] or bm_dict['hit_self']
            # Unclear whether flinching also resets Multiturn
            # reset_mlt = (bm_dict['fully_przd'] or bm_dict['hit_self']
            #              or bm_dict['flinched'])
            if reset_mlt:
                pkmn.sm.reset_counter('multiturn')
            decrement_mlt = ((not bm_dict['asleep_frozen'])
                             and (not bm_dict['trap_active']))
            if decrement_mlt:
                msg = pkmn.sm.decrement_counter('multiturn')
                post_message(msg)

    def apply_all_recurring_damage(self, user, other):
        """
        Apply recurring damage from burn, poison, leech seed
        """
        if user.sm.status in ['BRN', 'PSN', 'TXC']:
            self.apply_one_recurring_damage(user)
        if user.sm.get_flag('seed'):
            dmg = self.apply_one_recurring_damage(user, seed=True)
            self.seed_heal(other, dmg)

    def apply_one_recurring_damage(self, target, seed=False):
        counter = target.sm.get_counter('toxic')
        toxic_active = counter.val
        toxic_N = counter.cval
        damage = toxic_N*(target.max_hp//16)
        # Always do at least 1 HP of damage
        if damage == 0:
            damage = 1
        damage = min(damage, target.current_hp)
        target.current_hp -= damage
        if seed:
            message = f'{target.name}\'s health was drained!'
            # message = (f'{target.name}\'s health was drained! (-{damage} HP,'
            #            f' N={toxic_N})')
        else:
            message = f'{target.name} was affected by its '
            if target.sm.status == 'BRN':
                message += 'burn!'
                # message += f'burn! (-{damage}, N={toxic_N})'
            elif target.sm.status in ['PSN', 'TXC']:
                message += 'poison!'
                # message += f'poison! (-{damage}, N={toxic_N})'
            else:
                raise ValueError('Called apply_one_recurring_damage() on '
                                 f'healthy Pokemon: name={target.name}, '
                                 f'status={target.sm.status}')
        if globals.DEBUG:
            message += f'\n(-{damage} HP, N = {toxic_N})'
        post_message(message)
        if toxic_active:
            target.sm.increment_toxic()
        return damage

    def seed_heal(self, target, amount):
        target.current_hp += amount
        post_message(f'{target.name} was healed!')

    def check_for_faints(self, user, other):
        something_fainted = False
        if user.is_fainted() or other.is_fainted():
            something_fainted = True
        return something_fainted

    def take_turn_using_move(self, move, user, other, first=False):
        """
        Handles all aspects of one Pokemon using a move during its turn. This
        includes:
            - determining whether the Pokemon can move
            - updating the Pokemon's status counters and flags
            - using the selected move (if the Pokemon can)
            - checking for faints due to the move used, and determining what
                cases should be applied at the end of the round
            - taking recurring damage (burn, poison, leech seed) after using
                the move; or, if the Pokemon cannot use its move, flagging that
                the Pokemon should take recurring damage at the end of the
                round
            - determining whether any trapping damage should be applied at the
                end of the round
        Returns (something_fainted, pkmn_included_in_end_round).
        """

        l_pkmn = []
        move_caused_faint = False
        RD_caused_faint = False
        # Determine can/can't move and update status counters
        bmd = self.before_move(user, other)
        if bmd['can_move']:
            # Use the move
            self.mu.apply_move(move, user, other, first)
            # If the move caused a faint, recurring damage is skipped
            move_caused_faint = self.check_for_faints(user, other)
            if not move_caused_faint:
                self.after_move(user, other)
                RD_caused_faint = self.check_for_faints(user, other)
        else:
            # user should take recurring damage at the end of the round
            l_pkmn.append(user)
        something_fainted = move_caused_faint or RD_caused_faint
        return (something_fainted, l_pkmn)
