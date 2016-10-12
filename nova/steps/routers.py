from autostepler import dock


class RouterSteps(object):
    """Router steps."""

    @dock.outlet.router.create
    def create_router(self, router_name, distributed=False, check=True):
        pass

    @dock.inlet.router.create
    @dock.outlet.router.delete
    def delete_router(self, router, check=True):
        pass

    @dock.outlet.router.set_gateway
    def set_gateway(self, router, network, check=True):
        pass

    @dock.inlet.router.set_gateway
    @dock.outlet.router.unset_gateway
    def clear_gateway(self, router, check=True):
        pass
