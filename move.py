import globals


class Move:
    def __init__(self, name):
        d = globals.get_move_dict(name)
        if not d:
            raise KeyError(f'Move(): name = {name} not found!')
        for key, value in d.items():
            setattr(self, key, value)
        self._pp = self.max_pp

    @property
    def pp(self):
        return self._pp

    @pp.setter
    def pp(self, val):
        self._pp = val
