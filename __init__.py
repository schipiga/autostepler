class Helper():

    def __init__(self, dock_type):
        self._dock_type = dock_type
        self._vals = []

    def __getattr__(self, name):
        self._vals.append(name)
        return self

    def __call__(self, func):
        if not hasattr(func, self._dock_type):
            setattr(func, self._dock_type, {})
        getattr(func, self._dock_type).update(dict([self._vals]))
        self._vals[:] = []
        return func


class Dock(object):
    inlet = Helper('inlet')
    outlet = Helper('outlet')

dock = Dock()
