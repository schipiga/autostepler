def pytest_generate_tests(metafunc):
    if 'test_case' in metafunc.fixturenames:
        metafunc.parametrize('test_case', ['a', 'b', 'c'])


def pytest_configure(config):
    all_steps = []

    last_steps = []

    last_step = last_steps[0]

    resources = get_resources(last_step)

    test_case = []
    test_case.append(last_step)

    for resource in resources:
        step = get_step(resource)
        test_case.append(step)
