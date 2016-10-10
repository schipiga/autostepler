import pkgutil
import importlib
import inspect
import collections
import json

RESOURCES = {'server'}


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
    last_steps = _get_last_steps()

    cases = []

    for last_step in last_steps:
        test_case = TestCase()
        step_data = _retrieve_step_data(last_step)

        resources = set(step_data['args']) & RESOURCES
        if resources:
            cleanup = step_data
        else:
            test_case.add_step(step_data)

        for resource in resources:
            step_data = _get_step_by_resource(resource)
            if cleanup:
                step_data['cleanup'] = cleanup
            test_case.add_step(step_data)

        cases.append(test_case.to_json())

    import ipdb; ipdb.set_trace()


def _get_step_by_resource(resource):
    for step in ALL_STEPS:
        step_data = _retrieve_step_data(step)
        gain = step_data['gain']
        if gain[0] == resource and gain[1]:
            return step_data


def _retrieve_step_data(step):
    args = [arg for arg in inspect.getargspec(step).args if arg != 'self']

    gain = None
    output = getattr(step, 'output', None)
    if output:
        for k, v in output.iteritems():
            if v == 'create':
                gain = (k, True)
            if v == 'delete':
                gain = (k, False)

    od = collections.OrderedDict()
    od['step'] = step.__name__
    od['args'] = args
    od['gain'] = gain

    return od


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
