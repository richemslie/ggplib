from ggplib.player.random_player import RandomPlayer
from ggplib.player.legal_player import LegalPlayer
from ggplib.player.mcs import MCSPlayer
from ggplib.player.basic_cpp_players import CppRandomPlayer, CppLegalPlayer
from ggplib.player.simplemcts import SimpleMctsPlayer, GGTestPlayer1, GGTestPlayer2


python_players = {
    "random" : CppRandomPlayer,
    "legal" : CppLegalPlayer,
    "pyrandom" : RandomPlayer,
    "pylegal" : LegalPlayer,
    "pymcs" : MCSPlayer,
    "simplemcts" : SimpleMctsPlayer,
    "ggtest1" : GGTestPlayer1,
    "ggtest2" : GGTestPlayer2}


def get_player(player_type, player_name=None):
    if player_name is None:
        player_name = player_type

    return python_players[player_type](player_name)
