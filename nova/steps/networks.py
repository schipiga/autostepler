from autostepler import dock


class NetworkSteps(object):
    """Network steps."""

    @dock.outlet.network.create
    def create_network(self, network_name, check=True):
        pass

    @dock.inlet.network.create
    @dock.outlet.network.delete
    def delete_network(self, network, check=True):
        pass
