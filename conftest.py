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
    step_nodes = _attach_cleanups(step_nodes)
    step_nodes = _sort_nodes(step_nodes)

    test_cases = _compose_test_cases(step_nodes)
    print_test_cases(test_cases)
    import ipdb; ipdb.set_trace()


def _sort_nodes(step_nodes):
    other_nodes = [node for node in step_nodes if not node['name'].startswith('create_')]
    other_nodes.sort(key=lambda node: node['name'])
    create_nodes = [node for node in step_nodes if node['name'].startswith('create_')]
    create_nodes.sort(key=lambda node: node['name'])
    return [{'is_used': False, 'step': step} for step in other_nodes + create_nodes]


def _compose_test_cases(step_nodes):

    def _get_step_matcher(step_inlet, resource_name):
        in_resource_status = step_inlet.get(resource_name)
        if in_resource_status:
            return (resource_name, in_resource_status)
        else:
            return (resource_name, 'create')

    def _get_join_steps(step):
        if step['cleanup']:
            return [step, step['cleanup']]
        else:
            return [step]

    def _set_join_step_in_test_case(step_name):
        if not test_case_step[0]:

            for idx, test_case in enumerate(test_cases):
                result = _get_joined_step_from_test_case(
                    test_case, step_name)
                if result:
                    test_case_step[0] = result
                    test_case_step[0]['case_index'] = idx
            return True

        else:
            case_idx = test_case_step[0]['case_index']
            result = _get_joined_step_from_test_case(
                test_cases[case_idx], step_name)

            if result:
                if test_case_step[0]['index'] < result['index']:
                    test_case_step[0] = result
                    test_case_step[0]['case_index'] = case_idx
                return True
            else:
                return False

    def _compose(head_step):
        step_inlet = head_step['inlet']
        resource_names = sorted(set(head_step['args']) & REGISTERED_RESOURCES)

        for resource_name in resource_names:
            step_matcher = _get_step_matcher(step_inlet, resource_name)
            is_matched = False

            for node in step_nodes[:]:
                required_step = copy.deepcopy(node['step'])

                for join_step in _get_join_steps(required_step):

                    if step_matcher not in join_step['outlet'].items():
                        break

                    is_matched = True
                    is_join_step_set = False

                    if node['is_used']:
                        is_join_step_set = _set_join_step_in_test_case(
                            join_step['name'])

                    if not is_join_step_set:
                        join_step['step'] = head_step
                        node['is_used'] = True
                        head_step = _compose(required_step)

                    if is_matched:
                        break

                if is_matched:
                    break

        return head_step

    test_cases = []
    for node in step_nodes[:]:
        if node['is_used']:
            continue

        step = copy.deepcopy(node['step'])

        test_case_step = [None]
        step = _compose(step)

        if test_case_step[0]:
            test_case_step[0]['step']['step'] = step
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
    return step_nodes


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


def _get_joined_step_from_test_case(step, name):
    """Get step from test case to join to him.

    If step is usaged already in test, let's try to find it and to join in
    testcase.
    """
    def flatify(step, bucket=None):
        if not step:
            return

        bucket = [] if bucket is None else bucket
        bucket.append(step)

        flatify(step['step'], bucket)
        flatify(step['cleanup'], bucket)

        return bucket

    flat_steps = flatify(step)  # get plain list of steps tree

    for idx, flat_step in enumerate(flat_steps):
        if flat_step['name'] == name:

            while flat_step['step']:
                flat_step = flat_step['step']  # find a step to get in queue

            name = flat_step['name']
            break
    else:
        return  # used step is not found in current test case

    for idx, flat_step in enumerate(flat_steps):
        if flat_step['name'] == name:
            # return step to join with its index in plain list
            return {'index': idx, 'step': flat_step}

    else:
        import ipdb; ipdb.set_trace()
        # raise exception if nonsense happens
        raise Exception("Can't find step in plain list")


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
