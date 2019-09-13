from ggplib.non_gdl_games.draughts import spec


def create_board(fen):
    desc = spec.BoardDesc(10)
    spec_sm = spec.SM(desc)

    spec_sm.parse_fen(fen)

    from ggplib.db import lookup
    info = lookup.by_name("draughts_10x10")

    # will dupe / and reset
    sm = info.get_sm()

    base_state = sm.new_base_state()
    for i, v in enumerate(spec_sm.basestate):
        base_state.set(i, v)

    sm.update_bases(base_state)
    return sm, base_state


def get_whos_turn(bs):
    pysm = spec.SM(spec.BoardDesc(10),
                   basestate=bs.to_list())
    role = pysm.whos_turn()
    opponent = spec.WHITE if role == spec.BLACK else spec.BLACK
    return role, opponent


def print_board(bs):
    pysm = spec.SM(spec.BoardDesc(10),
                   basestate=bs.to_list())
    pysm.print_board()


def piece_count(bs, role):
    pysm = spec.SM(spec.BoardDesc(10),
                   basestate=bs.to_list())

    return len(list(pysm.all_for_role(role)))


def check_interim_status(bs):
    pysm = spec.SM(spec.BoardDesc(10),
                   basestate=bs.to_list())

    return pysm.check_interim_status()


def legal_mapping(role, legal):
    # XXX ugly hack using gencode
    from ggplib.non_gdl_games.draughts import gencode
    legal_black_index = gencode.GenCodeFn(10).legal_black_index

    board_desc = spec.BoardDesc(10)
    if role == 0:
        return board_desc.reverse_legal_mapping[role][legal]
    else:
        return board_desc.reverse_legal_mapping[role][legal + legal_black_index]
