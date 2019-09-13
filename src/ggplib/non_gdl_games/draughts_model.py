from pprint import pprint
from ggplib.statemachine.model import StateMachineModel

verbose = False


def create_sm_model(board_desc, breakthrough_mode=False):
    model = StateMachineModel()

    # add roles
    model.roles = ['white', 'black']

    # add base states
    for b in board_desc.bases:
        model.bases.append("(true %s)" % b)

    if verbose:
        pprint(model.bases)

    # add legals
    model.actions = [[], []]
    for legal in board_desc.all_legals:

        if breakthrough_mode and "king" in legal:
            continue

        action = legal.replace("legal", "does")
        if "white" in action:
            model.actions[0].append(action)
        else:
            model.actions[1].append(action)

    if verbose:
        print len(model.actions[0]), len(model.actions[1])
        pprint(model.actions)

    return model
