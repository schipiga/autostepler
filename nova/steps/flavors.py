from autostepler import dock


class FlavorSteps(object):

    @dock.outlet.flavor.create
    def create_flavor(self, flavor_name, ram, vcpus, disk, check=True):
        pass

    @dock.inlet.flavor.create
    @dock.outlet.flavor.delete
    def delete_flavor(self, flavor, check=True):
        pass
