from autostepler import dock


class SubnetSteps(object):
    """Subnet steps."""

    @dock.outlet.subnet.create
    def create_subnet(self, subnet_name, network, cidr, check=True):
        pass

    @dock.inlet.subnet.create
    @dock.outlet.subnet.delete
    def delete_subnet(self, subnet, check=True):
        pass
