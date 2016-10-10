import pkgutil
import importlib
import inspect
import json
import copy

RESOURCES = {'server'}

CLEANUP_PREFIXES = {'il', 'ir', 'im', 'in', 'un', 'dis', 'mis', 'non'}

CLEANUP_DICT = {
    'delete': 'create',
    'detach': 'attach',
    'resume': 'suspend'
}


class TestCase(object):

    def __init__(self):
        self._steps = []

    def add_step(self, step):
        self._steps.append(step)

    def to_json(self):
        return json.dumps({'steps': self._steps})


def pytest_generate_tests(metafunc):
    if 'test_case' in metafunc.fixturenames:
        metafunc.parametrize('test_case', ['a', 'b', 'c'])


def pytest_configure(config):
    # last_steps = _get_last_steps()

    steps_data = [_retrieve_step_data(step) for step in ALL_STEPS]

    for cleanup in steps_data[:]:
        okeys = set(cleanup['outlet'].keys())
        ikeys = set(cleanup['inlet'].keys())
        keys = okeys & ikeys

        match = None

        for key in keys:
            cval = cleanup['outlet'][key]
            sval = cleanup['inlet'][key]

            for k, v in CLEANUP_DICT.iteritems():
                if cval.startswith(k) and sval.startswith(v):
                    match = (key, sval)
                    break
            if cval.split(sval)[0] in CLEANUP_PREFIXES:
                match = (key, sval)

            if match:
                break

        if not match:
            continue

        for _step in steps_data:
            if match in _step['outlet'].items():
                _step['cleanup'] = cleanup
                steps_data.remove(cleanup)

    steps_data = [{'is_used': False, 'step': sd} for sd in steps_data]

    test_cases = []

    for sd in steps_data[:]:

        if sd['is_used']:
            continue

        step = copy.copy(sd['step'])

        tc_step = [None]

        def connect(step):
            resources = set(step['args']) & RESOURCES
            inlet = step['inlet']

            for resource in resources:
                cond = inlet.get(resource)
                if cond:
                    match = (resource, cond)
                else:
                    match = (resource, 'create')

                for _sd in steps_data:
                    _st = copy.copy(_sd['step'])

                    if match in _st['outlet'].items():
                        if _sd['is_used'] and not tc_step[0]:
                            for tc in test_cases:
                                _tc_step = _get_tc_step(tc, _st['name'])
                                if _tc_step:
                                    tc_step[0] = _tc_step

                        else:
                            _st['step'] = step
                            _st['is_used'] = True
                            step = connect(_st)

                    if match in _st['cleanup']['outlet'].items():
                        if _sd['is_used'] and not tc_step[0]:
                            for tc in test_cases:
                                _tc_step = _get_tc_step(tc, _st['name'])
                                if _tc_step:
                                    tc_step[0] = _tc_step

                        else:
                            _st['cleanup']['step'] = step
                            _st['is_used'] = True
                            step = connect(_st)

            return step

        step = connect(step)

        if tc_step[0]:
            tc_step[0]['step'] = step
        else:
            test_cases.append(step)
        sd['is_used'] = True


    import ipdb; ipdb.set_trace()


def print_test_cases(test_cases):
    indend = 0
    cleanups = []
    res = ''
    for step in test_cases:
        while step:
            res += ' ' * indend + step['name'] + '\n'
            if step['cleanup']:
                indend += 2
                cleanups.append(step['cleanup'])
            step = step['step']
        while cleanups:
            indend -= 2
            cleanup = cleanups.pop()
            res += ' ' * indend + cleanup['name'] + '\n'
        res += '\n'
    return res


def _get_tc_step(step, name):
    if not step:
        return
    if step['name'] == name:
        while step['step']:
            step = step['step']
        return step
    res1 = _get_tc_step(step['step'], name)
    res2 = _get_tc_step(step['cleanup'], name)
    return res1 or res2

def _get_step_by_resource(resource):
    for step in ALL_STEPS:
        step_data = _retrieve_step_data(step)
        gain = step_data['gain']
        if gain[0] == resource and gain[1]:
            return step_data


def _retrieve_step_data(step):
    args = [arg for arg in inspect.getargspec(step).args if arg != 'self']

    inlet = getattr(step, 'inlet', {})
    outlet = getattr(step, 'outlet', {})

    gain = None
    if outlet:
        for k, v in outlet.iteritems():
            if v == 'create':
                gain = (k, True)
            if v == 'delete':
                gain = (k, False)

    return {
        'name': step.__name__,
        'args': args,
        'gain': gain,
        'inlet': inlet,
        'outlet': outlet,
        'step': None,
        'cleanup': None,
    }


def _get_last_steps():
    return [step for step in ALL_STEPS if step.__name__.startswith('delete')]


def _get_steps():
    step_classes = []
    for _, pkg_name, is_pkg in pkgutil.iter_modules('.'):

        if not is_pkg:
            continue

        steps_module_name = 'autostepler.' + pkg_name + '.steps'
        try:
            steps_module = importlib.import_module(steps_module_name)
        except ImportError:
            continue

        for obj_name in steps_module.__all__:
            obj = getattr(steps_module, obj_name)

            if inspect.isclass(obj):
                step_classes.append(obj)

    return [getattr(cls, name) for cls in step_classes for name in dir(cls)
            if not name.startswith('_')]


ALL_STEPS = _get_steps()
