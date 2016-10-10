from autostepler import dock


class ServerSteps(object):

    @dock.outlet.server.create
    def create_server(self, server_name):
        server = {"type": "server", "name": server_name}
        print "Create server", server_name
        return server

    @dock.outlet.server.lock
    def lock_server(self, server):
        print "Lock server", server

    @dock.inlet.server.lock
    @dock.outlet.server.unlock
    def unlock_server(self, server):
        print "Unlock server", server

    @dock.outlet.server.attached
    def attach_volume(self, server, volume):
        print "Attach volume to", server

    @dock.inlet.server.attached
    @dock.outlet.server.detached
    def detach_volume(self, server):
        print "Detach volume from", server

    @dock.inlet.server.lock
    @dock.outlet.server.suspend
    def suspend_server(self, server):
        print "Suspend server", server

    @dock.inlet.server.suspend
    @dock.outlet.server.resume
    def resume_server(self, server):
        print "Resume server", server

    @dock.inlet.server.create
    @dock.outlet.server.delete
    def delete_server(self, server):
        print "Delete server", server
