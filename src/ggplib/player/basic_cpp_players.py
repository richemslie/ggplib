from ggplib import interface
from ggplib.player.proxy import ProxyPlayer


class CppRandomPlayer(ProxyPlayer):
    def meta_create_player(self):
        return interface.create_random_player(self.sm, self.match.our_role_index)


class CppLegalPlayer(ProxyPlayer):
    def meta_create_player(self):
        return interface.create_legal_player(self.sm, self.match.our_role_index)
