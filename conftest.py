import pkgutil
import importlib
import inspect
import json
import copy

REGISTERED_RESOURCES = set()

CLEANUP_PREFIXES = {'il', 'ir', 'im', 'in', 'un', 'dis', 'mis', 'non'}

CLEANUP_DICT = {
    'delete': 'create',
    'detach': 'attach',
    'resume': 'suspend'
}


def pytest_generate_tests(metafunc):
    if 'test_case' in metafunc.fixturenames:
        metafunc.parametrize('test_case', ['a', 'b', 'c'])


def pytest_configure(config):
    step_nodes = [_get_step_node(step) for step in ALL_STEPS]
    _attach_cleanups(step_nodes)
    step_nodes = [{'is_used': False, 'step': node} for node in step_nodes]

    test_cases = _compose_test_cases(step_nodes)
    print_test_cases(test_cases)
    import ipdb; ipdb.set_trace()


def _compose_test_cases(step_nodes):

    def _compose(step):
        resource_names = set(step['args']) & REGISTERED_RESOURCES
        inlet = step['inlet']

        for resource_name in resource_names:
            in_resource_status = inlet.get(resource_name)
            if in_resource_status:
                step_matcher = (resource_name, in_resource_status)
            else:
                step_matcher = (resource_name, 'create')

            for node in step_nodes[:]:
                prev_step = copy.copy(node['step'])

                if prev_step['cleanup']:
                    join_steps = (prev_step, prev_step['cleanup'])
                else:
                    join_steps = (prev_step,)

                for join_step in join_steps:
                    if step_matcher in join_step['outlet'].items():

                        if node['is_used']:
                            if test_case_idx[0]:
                                idx = test_case_idx[0]
                                _test_case_step = _get_test_case_step(
                                    test_cases[idx], join_step['name'])
                            else:
                                for idx, test_case in enumerate(test_cases):
                                    _test_case_step = _get_test_case_step(
                                        test_case, join_step['name'])

                            if _test_case_step:
                                if not test_case_step[0]:
                                    test_case_step[0] = _test_case_step
                                else:
                                    if (test_case_step[0][0] <
                                            _test_case_step[0]):
                                        test_case_step[0] = _test_case_step

                        else:
                            join_step['step'] = step
                            node['is_used'] = True
                            step = _compose(prev_step)
                        break
        return step

    test_cases = []
    for node in step_nodes[:]:
        if node['is_used']:
            continue

        step = copy.copy(node['step'])

        test_case_idx = [None]
        test_case_step = [None]
        step = _compose(step)

        if test_case_step[0]:
            test_case_step[0][1]['step'] = step
        else:
            test_cases.append(step)

        node['is_used'] = True
    return test_cases


def _attach_cleanups(step_nodes):
    for cleanup in step_nodes[:]:
        out_keys = set(cleanup['outlet'].keys())
        in_keys = set(cleanup['inlet'].keys())

        common_keys = out_keys & in_keys

        step_matchers = []

        for resource_name in common_keys:
            out_resource_status = cleanup['outlet'][resource_name]
            in_resource_status = cleanup['inlet'][resource_name]

            for key, val in CLEANUP_DICT.iteritems():
                if (out_resource_status.startswith(key) and
                        in_resource_status.startswith(val)):
                    step_matchers.append((resource_name, in_resource_status))
                    break

            prefix = out_resource_status.split(in_resource_status)[0]
            if prefix in CLEANUP_PREFIXES:
                step_matchers.append((resource_name, in_resource_status))

        assert len(step_matchers) < 2, "Too many resources are changed"

        if not step_matchers:
            continue

        for node in step_nodes[:]:
            if step_matchers[0] in node['outlet'].items():
                node['cleanup'] = cleanup
                step_nodes.remove(cleanup)
                break
        else:
            raise LookupError(
                "No setup step for cleanup {}".format(node['name']))


def print_test_cases(test_cases):
    indend = [0]
    res = ['']
    for step in test_cases:

        def flatify(step):
            if not step:
                return
            res[0] += ' ' * indend[0] + step['name'] + '\n'
            if step['cleanup']:
                indend[0] += 2
            flatify(step['step'])
            if step['cleanup']:
                indend[0] -= 2
            flatify(step['cleanup'])
        flatify(step)

        res[0] += '\n'

    print res[0]


def _get_test_case_step(step, name):

    result = []

    def flatify(step):
        if not step:
            return
        result.append(step)
        flatify(step['step'])
        flatify(step['cleanup'])

    flatify(step)

    for idx, flat_step in enumerate(result):
        if flat_step['name'] == name:
            while flat_step['step']:
                flat_step = flat_step['step']
            name = flat_step['name']
            break
    else:
        return

    for idx, flat_step in enumerate(result):
        if flat_step['name'] == name and not flat_step['step']:
            return (idx, flat_step)
    else:
        return


def _get_step_node(step):
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
                resource_name = obj.__name__.split('Steps')[0].lower()
                REGISTERED_RESOURCES.add(resource_name)
                step_classes.append(obj)

    return [getattr(cls, name) for cls in step_classes for name in dir(cls)
            if not name.startswith('_')]


ALL_STEPS = _get_steps()
