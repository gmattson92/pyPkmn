class Flag:
    """
    Defines common functionality for flags managing the state of a Pokemon.
    """
    def __init__(self, name, initial_val=False, **kwargs):
        self.name = name
        self._val = initial_val
        self.turn_on_string = ''
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


class StatusManager:
    """
    Manages internal flags and counters for a Pokemon. Interfaces with MoveUser
    to apply all relevant effects when a move is used.
    """
    def __init__(self, pkmn):
        self.pkmn = pkmn
        self._can_select_move = True
        self.flags = {}
        self.active_flags = []
        self.counters = {}
        self.active_counters = []
        # Non-volatile (major) status condition
        self.status = None
        d_sleep = {'name': 'sleep',
                   'initial_flag_val': False,
                   'initial_counter_val': 0,
                   'turn_on_string': f'{self.pkmn.name} fell asleep!',
                   'still_on_string': f'{self.pkmn.name} is fast asleep!',
                   'expire_string': f'{self.pkmn.name} woke up!'}
        self.counters[d_sleep['name']] = Counter(**d_sleep)
        # Now all the specific flags for status and move interactions:
        # status interactions
        d_confusion = {'name': 'confusion',
                       'initial_flag_val': False,
                       'initial_counter_val': 0,
                       'turn_on_string': f'{self.pkmn.name} became confused!',
                       'still_on_string': f'{self.pkmn.name} is confused!',
                       'expire_string':
                           f'{self.pkmn.name} snapped out of confusion!'}
        self.counters[d_confusion['name']] = Counter(**d_confusion)
        d_flinch = {'name': 'flinch',
                    'initial_flag_val': False,
                    'turn_on_string': f'{self.pkmn.name} flinched!'}
        self.flags[d_flinch['name']] = Flag(**d_flinch)
        d_disable = {'name': 'disable',
                     'initial_flag_val': False,
                     'initial_counter_val': 0,
                     'turn_on_string': f'{self.pkmn.name} became Disabled!',
                     'still_on_string': f'{self.pkmn.name} is Disabled!',
                     'expire_string': f'{self.pkmn.name} is Disabled no more!'}
        self.counters[d_disable['name']] = Counter(**d_disable)
        d_seed = {'name': 'seed',
                  'initial_flag_val': False,
                  'turn_on_string': f'{self.pkmn.name} was seeded!'}
        self.flags[d_seed['name']] = Flag(**d_seed)
        d_toxic = {'name': 'toxic',
                   'initial_flag_val': False,
                   'initial_counter_val': 1,
                   'turn_on_string': f'{self.pkmn.name} was badly Posioned!'}
        self.counters[d_toxic['name']] = ToxicCounter(**d_toxic)
        # stat interactions
        d_lightscreen = {'name': 'lightscreen',
                         'initial_flag_val': False,
                         'turn_on_string':
                         f'{self.pkmn.name} put up a Lightscreen!'}
        self.flags[d_lightscreen['name']] = Flag(**d_lightscreen)
        d_reflect = {'name': 'reflect',
                     'initial_flag_val': False,
                     'turn_on_string': f'{self.pkmn.name} put up a Reflect!'}
        self.flags[d_reflect['name']] = Flag(**d_reflect)
        # move selection disabled
        d_recharge = {'name': 'recharge',
                      'initial_flag_val': False,
                      'expire_string': f'{self.pkmn.name} has to recharge!',
                      'can_select_move': False}
        self.flags[d_recharge['name']] = Flag(**d_reflect)
        d_multiturn = {'name': 'multiturn',
                       'initial_flag_val': False,
                       'initial_counter_val': 0,
                       'still_on_string':
                       f'{self.pkmn.name} is thrashing about!',
                       'can_select_move': False}
        self.counters[d_multiturn['name']] = Counter(**d_multiturn)
        d_multiturn = {'name': 'multiturn',
                       'initial_flag_val': False,
                       'initial_counter_val': 0,
                       'still_on_string':
                       f'{self.pkmn.name} is thrashing about!',
                       'can_select_move': False}
        self.counters[d_multiturn['name']] = Counter(**d_multiturn)
        d_trapping = {'name': 'trapping',
                      'initial_flag_val': False,
                      'initial_counter_val': 0,
                      'can_select_move': False}
        self.counters[d_trapping['name']] = Counter(**d_trapping)
        d_trapped = {'name': 'trapped',
                     'initial_flag_val': False,
                     'initial_counter_val': 0,
                     'can_select_move': False}
        self.counters[d_trapped['name']] = Counter(**d_trapped)
        self.two_turn = False
        d_two_turn = {'name': 'two_turn',
                      'initial_flag_val': False,
                      'can_select_move': False}
        self.flags[d_two_turn['name']] = Flag(**d_two_turn)

    def update_can_select_move(self):
        # Update based on active flags
        new_val = True
        for flag in self.active_flags:
            if not flag.can_select_move:
                new_val = False
        for counter in self.active_counters:
            if not counter.can_select_move:
                new_val = False
        self._can_select_move = new_val

    @property
    def can_select_move(self):
        self.update_can_select_move()
        return self._can_select_move

    @can_select_move.setter
    def can_select_move(self, val):
        self._can_select_move = val

    def get_flag(self, name):
        flag = None
        try:
            flag = self.flags[name]
        except KeyError:
            pass
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
            pass
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
            # Remove from activate counters
            self.active_counters.remove(counter)
            # For waking up from sleep, update pokemon's non-volatile status
            if name == 'sleep':
                self.status = None
        return message

    def increment_toxic(self):
        counter = self.get_counter('toxic')
        return counter.increment()
