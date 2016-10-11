from autostepler import dock


class SecurityGroupSteps(object):
    """Security group steps."""

    @dock.outlet.securitygroup.create
    def create_group(self, group_name, description='', check=True):
        pass

    @dock.outlet.securitygroup.add_rules
    def add_group_rules(self, securitygroup, rules, check=True):
        pass

    @dock.inlet.securitygroup.create
    @dock.outlet.securitygroup.delete
    def delete_group(self, securitygroup, check=True):
        pass
