from autostepler import dock


class KeypairSteps(object):
    """Keypair steps."""

    @dock.outlet.keypair.create
    def create_keypair(self, keypair_name, check=True):
        pass

    @dock.inlet.keypair.create
    @dock.outlet.keypair.delete
    def delete_keypair(self, keypair, check=True):
        pass
