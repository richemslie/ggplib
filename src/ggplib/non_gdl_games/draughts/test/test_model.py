import pprint
from ggplib.non_gdl_games.draughts import desc, model


def test_model():
    m = model.create_sm_model(desc.BoardDesc(10))
    pprint.pprint(m.roles)
    pprint.pprint(m.bases)
    pprint.pprint(m.actions)
