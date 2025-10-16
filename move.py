import globals


class Move:
    def __init__(self, name):
        d = globals.get_moves_dict(name)
        for key, value in d.items():
            setattr(self, key, value)
        self._pp = self.max_pp

    @property
    def pp(self):
        return self._pp

    @pp.setter
    def pp(self, val):
        self._pp = val
