from autostepler import dock


class ServerSteps(object):

    @dock.output.server.create
    def create_server(self, server_name):
        server = {"type": "server", "name": server_name}
        print "Create server", server_name
        return server

    @dock.input.server.active
    @dock.output.server.delete
    def delete_server(self, server):
        print "Delete server", server
