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

    # @steps_checker.step
    # def add_subnet_interface(self, router, subnet, check=True):
    #     """Step to add router to subnet interface.

    #     Args:
    #         router (dict): router
    #         subnet (dict): subnet
    #     """
    #     self._client.add_subnet_interface(router_id=router['id'],
    #                                       subnet_id=subnet['id'])
    #     if check:
    #         self.check_interface_subnet_presence(router, subnet)

    # @steps_checker.step
    # def remove_subnet_interface(self, router, subnet, check=True):
    #     """Step to remove router to subnet interface.

    #     Args:
    #         router (dict): router
    #         subnet (dict): subnet
    #     """
    #     self._client.remove_subnet_interface(router_id=router['id'],
    #                                          subnet_id=subnet['id'])
    #     if check:
    #         self.check_interface_subnet_presence(router, subnet, present=False)
