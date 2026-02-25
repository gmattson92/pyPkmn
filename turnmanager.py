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
    is trapping/binding, which changes in Battle.end_round().
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

    def fully_prz(self, pkmn):
        """
        Checks if pkmn is fully paralyzed and prevented from moving this turn.
        If so, posts message. Returns bool.
        """
        fully_prz = False
        if pkmn.sm.status == 'PRZ':
            fully_prz = globals.rng_check(globals.FULL_PRZ_CHANCE)
            if fully_prz:
                post_message(f'{pkmn.name} is fully paralyzed!')
        return fully_prz

    def can_move_status(self, pkmn):
        """
        Checks if pkmn is prevented from moving by a non-volatile status
        condition and, if so, posts the appropriate message. Also handles
        decrementing the sleep counter.
        Returns (can_move, asleep_frozen, fully_paralyzed). The latter two are
        needed for deciding how to handle several other status counters.
        """
        asleep_frozen = False
        fully_prz = False
        if pkmn.sm.status == 'SLP':
            can_move_status = False
            asleep_frozen = True
            message = pkmn.sm.decrement_counter('sleep')
            post_message(message)
        elif pkmn.sm.status == 'FRZ':
            can_move_status = False
            asleep_frozen = True
            post_message(f'{pkmn.name} is frozen solid!')
        elif pkmn.sm.status == 'PRZ':
            fully_prz = self.fully_prz(pkmn)
            if fully_prz:
                can_move_status = False
            else:
                can_move_status = True
        else:
            can_move_status = True

        return (can_move_status, asleep_frozen, fully_prz)

    def can_move_flinch(self, pkmn):
        if pkmn.sm.get_flag('flinch'):
            can_move_flinch = False
            post_message(f'{pkmn.name} flinched!')
            # Reset the flinch flag
            pkmn.sm.reset_flag('flinch')
        else:
            can_move_flinch = True
        return can_move_flinch

    def can_move_recharge(self, pkmn):
        if pkmn.sm.get_flag('recharge'):
            can_move_recharge = False
            post_message(f'{pkmn.name} has to recharge!')
            # Reset the recharge flag, unless pkmn is frozen
            if pkmn.sm.status != 'FRZ':
                pkmn.sm.reset_flag('recharge')
        else:
            can_move_recharge = True
        return can_move_recharge

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
            - decrementing the Multiturn counter & checking for expiration
        Note that the Trapping/Trapped counters decrement during end_round,
        rather than here like all the other counters; likewise for the Toxic
        counter incrementing. However, Trap counters can be reset here
        depending on other status effects.

        Returns dict with overall can/can't move determination and details on
        which checks pass and fail. Valid keys are:
            - 'can_move'
            - 'asleep_frozen'
            - 'flinched'
            - 'recharging'
            - 'hit_self'
            - 'trap_active'
        """
        ret = {}
        # Check non-volatile status and decrement sleep counter
        can_move_status, asleep_frozen, fully_prz = self.can_move_status(user)
        ret['asleep_frozen'] = asleep_frozen
        ret['fully_prz'] = fully_prz

        # Check for flinching
        can_move_flinch = self.can_move_flinch(user)
        ret['flinched'] = not can_move_flinch

        # Check for recharge turn
        can_move_recharge = self.can_move_recharge(user)
        ret['recharging'] = not can_move_recharge

        # Check for trapping moves
        if user.sm.get_counter('trapped') or user.sm.get_counter('trapping'):
            trap_active = True
        else:
            trap_active = False
        ret['trap_active'] = trap_active

        # Overall can/can't move
        can_move_nonstatus = can_move_flinch and can_move_recharge
        can_move = can_move_status and can_move_nonstatus
        ret['can_move'] = can_move

        # Confusion and Disable, which are paused during sleep, freeze,
        # flinches, and recharge turns, but do decrement during full paralysis
        # and trapping turns
        decrement_cnf_dsb = ((not asleep_frozen)
                             and can_move_flinch
                             and can_move_recharge)
        if decrement_cnf_dsb:
            # Decrement Disable first, because the confusion check happens
            # right after this
            if user.sm.get_counter('disable'):
                msg = user.sm.decrement_counter('disable')
                post_message(msg)
            if user.sm.get_counter('confusion'):
                msg = user.sm.decrement_counter('confusion')
                post_message(msg)

        # Check for pkmn hitting itself in confusion (but skip this if pkmn
        # can't move for another reason)
        hit_self = False
        if can_move:
            hit_self = self.confusion_check(user, other)
        ret['hit_self'] = hit_self

        # Multiturn, which is more complicated -- hits in confusion and full
        # paralysis reset the move completely; sleep, freeze and trapped all
        # pause the move but do not decrement the counter.
        if user.sm.get_counter('multiturn'):
            reset_mlt = fully_prz or hit_self
            # Unclear whether flinching also resets Multiturn
            # reset_mlt = fully_prz or hit_self or (not can_move_flinch)
            if reset_mlt:
                user.sm.reset_counter('multiturn')
            decrement_mlt = (not asleep_frozen) and (not trap_active)
            if decrement_mlt:
                msg = user.sm.decrement_counter('multiturn')
                post_message(msg)

        return ret

    def after_move(self, user, other):
        """
        Apply effects that occur after using a move:
            - Recurring damage (burn, poison/toxic, leech seed)
        """
        self.apply_all_recurring_damage(user, other)

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
