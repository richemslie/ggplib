from pprint import pprint
from ggplib.statemachine.model import StateMachineModel

verbose = False


def create_sm_model(sz):
    model = StateMachineModel()

    # add roles
    model.roles = ['black', 'white']

    # add base states
    alpha = "abcdefghijklmnopqrstuvwxyz"
    assert len(alpha) == 26

    model.actions = [[], []]
    model.actions[0].append("(does black noop)")
    model.actions[1].append("(does white noop)")
    model.actions[1].append("(does white swap)")

    for ii in range(sz):
        for jj in range(sz):
            x = alpha[jj]
            y = str(ii + 1)
            model.bases.append("(true (cell black %s %s))" % (x, y))
            model.bases.append("(true (cell blackNorth %s %s))" % (x, y))
            model.bases.append("(true (cell blackSouth %s %s))" % (x, y))
            model.bases.append("(true (cell white %s %s))" % (x, y))
            model.bases.append("(true (cell whiteWest %s %s))" % (x, y))
            model.bases.append("(true (cell whiteEast %s %s))" % (x, y))
            model.bases.append("(true (pad_0 %s %s))" % (x, y))
            model.bases.append("(true (pad_1 %s %s))" % (x, y))

            model.actions[0].append("(does black (place %s %s))" % (x, y))
            model.actions[1].append("(does white (place %s %s))" % (x, y))

    # add meta
    model.bases.append("(true (control black))")
    model.bases.append("(true (control white))")
    model.bases.append("(true black_connected)")
    model.bases.append("(true white_connected)")
    model.bases.append("(true can_swap)")
    model.bases.append("(true meta_pad0)")
    model.bases.append("(true meta_pad1)")
    model.bases.append("(true meta_pad2)")

    if verbose:
        pprint(model.bases)
        pprint(model.actions)

    return model
