class Flag:
    """
    Defines common functionality for flags managing the state of a Pokemon.
    """
    def __init__(self, name, initial_val=False, **kwargs):
        self.name = name
        self._val = initial_val
        self.turn_on_string = ''
        atts = ['turn_on_string', 'still_on_string',
                'expire_string', 'reset_string', 'can_select_move']
        for att in atts:
            val = '' if att != 'can_select_move' else True
            if att in kwargs:
                val = kwargs[att]
            setattr(self, att, val)
        '''
        if 'turn_on_string' in kwargs:
            self.turn_on_string = kwargs['turn_on_string']
        if 'still_on_string' in kwargs:
            self.still_on_string = kwargs['still_on_string']
        self.expire_string = ''
        if 'expire_string' in kwargs:
            self.expire_string = kwargs['expire_string']
        self.reset_string = ''
        if 'reset_string' in kwargs:
            self.reset_string = kwargs['reset_string']
        self.can_select_move = True
        if 'can_select_move' in kwargs:
            self.can_select_move = kwargs['can_select_move']
        '''

    def __bool__(self):
        return self._val

    @property
    def val(self):
        return self._val

    @val.setter
    def val(self, new_val):
        self._val = new_val

    def turn_on(self):
        self.val = True
        return self.turn_on_string

    def expire(self):
        self.val = False
        return self.expire_string

    def reset(self):
        self.val = False
        return self.reset_string


class Counter(Flag):
    """
    Defines common functionality for turn counters representing the duration
    of an effect on a Pokemon's status.
    """
    def __init__(self, name, initial_flag_val=False,
                 initial_counter_val=0, **kwargs):
        super().__init__(name, initial_flag_val, **kwargs)
        self._cval = initial_counter_val

    @property
    def cval(self):
        return self._cval

    @cval.setter
    def cval(self, new_val):
        if self._cval < 0:
            raise ValueError(f'Counter {self.name} updated to negative value '
                             f'{new_val}!')
        self._cval = new_val

    def decrement(self):
        # Double check that the counter is nonzero
        if self.cval < 1:
            raise ValueError(f'In decrement() for Counter {self.name}: '
                             f'current cval={self.cval}')
        # Then decrement counter, and reset status/flag if counter is 0
        self.cval -= 1
        message = ''
        if self.cval == 0:
            message = self.expire()
        else:
            message = self.still_on_string
        return message

    def reset(self):
        message = super().reset()
        self.cval = 0
        return message


class ToxicCounter(Counter):
    """
    Special behavior for the toxic/leech seed/burn N, which increments instead
    of decrementing.
    """
    def __init__(self, name='toxic', initial_flag_val=False,
                 initial_counter_val=1, **kwargs):
        super().__init__(name, initial_flag_val, **kwargs)
        self._cval = initial_counter_val

    def increment(self):
        if self.cval < 15:
            self.cval += 1

    def reset(self):
        message = super().reset()
        self.cval = 1
        return message


class StatusManager:
    """
    Manages internal flags and counters for a Pokemon. Interfaces with MoveUser
    to apply all relevant effects when a move is used.
    """
    def __init__(self, pkmn):
        self.pkmn = pkmn
        self._can_select_move = True
        self.flags = self._init_flags()
        self.counters = self._init_counters()
        self.active_flags = []
        self.active_counters = []
        # Non-volatile (major) status condition
        self._status = None

    @property
    def status(self):
        return self._status

    @status.setter
    def status(self, val):
        self._status = val

    def retreat(self):
        """
        Resets status flags and counters when the Pokemon swaps out.
        """
        # Convert Toxic to regular Poison:
        if self._status == 'TXC':
            self._status = 'PSN'
        # Reset all other flags and counters, except the sleep counter
        for flag in self.active_flags:
            flag.reset()
        for counter in self.active_counters:
            if counter.name != 'sleep':
                counter.reset()

    @property
    def can_select_move(self):
        self._update_can_select_move()
        return self._can_select_move

    '''
    @can_select_move.setter
    def can_select_move(self, val):
        self._can_select_move = val
    '''

    def get_flag(self, name):
        flag = None
        try:
            flag = self.flags[name]
        except KeyError:
            print(f'No Flag {name} found!')
        return flag

    def turn_on_flag(self, name):
        flag = self.get_flag(name)
        self.active_flags.append(flag)
        return flag.turn_on()

    def reset_flag(self, name):
        flag = self.get_flag(name)
        self.active_flags.remove(flag)
        return flag.reset()

    def get_counter(self, name):
        counter = None
        try:
            counter = self.counters[name]
        except KeyError:
            print(f'No Counter {name} found!')
        return counter

    def turn_on_counter(self, name, initial_cval):
        counter = self.get_counter(name)
        self.active_counters.append(counter)
        message = counter.turn_on()
        counter.cval = initial_cval
        return message

    def reset_counter(self, name):
        counter = self.get_counter(name)
        self.active_counters.remove(counter)
        return counter.reset()

    def decrement_counter(self, name):
        counter = self.get_counter(name)
        message = counter.decrement()
        if not counter.val:
            # Remove from active counters
            self.active_counters.remove(counter)
            # For waking up from sleep, update pokemon's non-volatile status
            if name == 'sleep':
                self._status = None
        return message

    def increment_toxic(self):
        counter = self.get_counter('toxic')
        return counter.increment()

    def _init_flags(self):
        flags = {}
        # Volatile (minor) status
        flags['flinch'] = Flag(**(self._d_flinch()))
        flags['seed'] = Flag(**(self._d_seed()))
        # Stat-changing interactions
        flags['lightscreen'] = Flag(**(self._d_lightscreen()))
        flags['reflect'] = Flag(**(self._d_reflect()))
        # Move selection disabled
        flags['recharge'] = Flag(**(self._d_recharge()))
        flags['two_turn'] = Flag(**(self._d_two_turn()))
        return flags

    def _init_counters(self):
        counters = {}
        # Non-volatile (major) status
        counters['sleep'] = Counter(**(self._d_sleep()))
        counters['toxic'] = ToxicCounter(**(self._d_toxic()))
        # Volatile (minor) status
        counters['confusion'] = Counter(**(self._d_confusion()))
        counters['disable'] = Counter(**(self._d_disable()))
        # Other move interactions
        counters['multiturn'] = Counter(**(self._d_multiturn()))
        counters['trapping'] = Counter(**(self._d_trapping()))
        counters['trapped'] = Counter(**(self._d_trapped()))
        return counters

    def _d_flinch(self):
        return {'name': 'flinch',
                'initial_flag_val': False,
                'turn_on_string': f'{self.pkmn.name} flinched!'}

    def _d_seed(self):
        return {'name': 'seed',
                'initial_flag_val': False,
                'turn_on_string': f'{self.pkmn.name} was seeded!'}

    def _d_lightscreen(self):
        return {'name': 'lightscreen',
                'initial_flag_val': False,
                'turn_on_string':
                f'{self.pkmn.name} put up a Lightscreen!'}

    def _d_reflect(self):
        return {'name': 'reflect',
                'initial_flag_val': False,
                'turn_on_string': f'{self.pkmn.name} put up a Reflect!'}

    def _d_recharge(self):
        return {'name': 'recharge',
                'initial_flag_val': False,
                'expire_string': f'{self.pkmn.name} has to recharge!',
                'can_select_move': False}

    def _d_two_turn(self):
        return {'name': 'two_turn',
                'initial_flag_val': False,
                'can_select_move': False}

    def _d_sleep(self):
        return {'name': 'sleep',
                'initial_flag_val': False,
                'initial_counter_val': 0,
                'turn_on_string': f'{self.pkmn.name} fell asleep!',
                'still_on_string': f'{self.pkmn.name} is fast asleep!',
                'expire_string': f'{self.pkmn.name} woke up!'}

    def _d_confusion(self):
        return {'name': 'confusion',
                'initial_flag_val': False,
                'initial_counter_val': 0,
                'turn_on_string': f'{self.pkmn.name} became confused!',
                'still_on_string': f'{self.pkmn.name} is confused!',
                'expire_string': f'{self.pkmn.name} snapped out of confusion!'}

    def _d_disable(self):
        return {'name': 'disable',
                'initial_flag_val': False,
                'initial_counter_val': 0,
                'turn_on_string': f'{self.pkmn.name} became Disabled!',
                'still_on_string': f'{self.pkmn.name} is Disabled!',
                'expire_string': f'{self.pkmn.name} is Disabled no more!'}

    def _d_toxic(self):
        return {'name': 'toxic',
                'initial_flag_val': False,
                'initial_counter_val': 1,
                'turn_on_string': f'{self.pkmn.name} was badly Posioned!'}

    def _d_multiturn(self):
        return {'name': 'multiturn',
                'initial_flag_val': False,
                'initial_counter_val': 0,
                'still_on_string':
                f'{self.pkmn.name} is thrashing about!',
                'expire_string': f'{self.pkmn.name} is fatigued!',
                'can_select_move': False}

    def _d_trapping(self):
        return {'name': 'trapping',
                'initial_flag_val': False,
                'initial_counter_val': 0,
                'can_select_move': False}

    def _d_trapped(self):
        return {'name': 'trapped',
                'initial_flag_val': False,
                'initial_counter_val': 0,
                'can_select_move': False}

    def _update_can_select_move(self):
        # Update based on active flags
        new_val = True
        for flag in self.active_flags:
            if not flag.can_select_move:
                new_val = False
        for counter in self.active_counters:
            if not counter.can_select_move:
                new_val = False
        self._can_select_move = new_val
