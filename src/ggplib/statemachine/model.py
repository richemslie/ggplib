from collections import OrderedDict

class StateMachineModel(object):
    def __init__(self):
        # will populate later
        self.roles = []
        self.bases = []
        self.actions = []

    def get_roles(self):
        return self.roles

    def to_description(self):
        d = OrderedDict()
        d['roles'] = self.roles
        d['bases'] = self.bases
        d['actions'] = self.actions
        return d

    def from_description(self, info):
        self.roles = info["roles"]
        self.bases = info["bases"]
        self.actions = info["actions"]

    def from_propnet(self, propnet):
        self.roles = [ri.role for ri in propnet.role_infos]
        self.bases = []
        self.actions = [[] for ri in propnet.role_infos]

        for b in propnet.base_propositions:
            self.bases.append(str(b.meta.gdl))

        for ri in propnet.role_infos:
            actions = self.actions[ri.role_index]

            for a in ri.inputs:
                actions.append(str(a.meta.gdl))

    def basestate_to_str(self, bs):
        ' from basestate to string '
        return " ".join([self.bases[i] for i in range(bs.len()) if bs.get(i)])
