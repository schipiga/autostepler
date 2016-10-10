import six


def test_executor(test_case):
    """Test executor."""
    ctx = {}
    cleanups = []
    root_cause = [None]

    def exec_step(step, args, resource):
        kwgs = {}
        for i in args:
            kwgs = {i: ctx[i]}
            try:
                result = step(**kwgs)
            except Exception as e:
                root_cause[0] = e
            else:
                if resource:
                    if resource[1]:
                        ctx[resource] = result
                    else:
                        del ctx[resource]

    for step, args, resource, cleanup in test_case:
        exec_step(step, args, resource)
        if root_cause[0]:
            break
        cleanups.append(cleanup)

    while cleanups:
        exec_step(*cleanups.pop())

    if root_cause[0]:
        six.reraise(root_cause[0])
