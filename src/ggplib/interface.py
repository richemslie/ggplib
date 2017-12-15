import os
from cffi import FFI

from ggplib.util import log


def get_lib():
    # get the paths
    d = os.path.dirname
    local_path = os.path.join(d(d(os.path.abspath(__file__))), "cpp")

    def process_line(line):
        # pre-process a line.  Skip any lines with comments.  Replace strings in remap.
        if "//" in line:
            return line
        remap = {
            "StateMachine*" : "void*",
            "BaseState*" : "void*",
            "LegalState*" : "void*",
            "JointMove*" : "void*",
            "boolean" : "int",
            "PlayerBase*" : "void*",
            "DepthChargeTest*" : "void*",
        }

        for k, v in remap.items():
            if k in line:
                line = line.replace(k, v)
                line = line.rstrip()
        return line

    def get_lines(filename):
        # take subset of file (since it is c++, and want only the c portion
        emit = False
        for line in open(filename):
            if "CFFI START INCLUDE" in line:
                emit = True
            elif "CFFI END INCLUDE" in line:
                emit = False
            if emit:
                line = process_line(line)
                if line:
                    yield line

    # get ffi object, and lib object
    ffi = FFI()
    ffi.cdef("\n".join(get_lines(os.path.join(local_path, "interface.h"))))
    return ffi, ffi.verify('#include <interface.h>\n',
                           include_dirs=[local_path],
                           library_dirs=[local_path],
                           libraries=["rt", "ggplib_cpp"])


ffi, lib = get_lib()


###############################################################################
# wrappers of c++ classes
###############################################################################

class BaseState:
    def __init__(self, c_base_state):
        self.c_base_state = c_base_state

    def get(self, index):
        return lib.BaseState__get(self.c_base_state, index)

    def set(self, index, value):
        return lib.BaseState__set(self.c_base_state, index, value)

    def hash_code(self):
        return lib.BaseState__hashCode(self.c_base_state)

    def equals(self, other):
        return lib.BaseState__equals(self.c_base_state, other.c_base_state)

    def assign(self, other):
        lib.BaseState__assign(self.c_base_state, other.c_base_state)

    def len(self):
        return lib.BaseState__len(self.c_base_state)

    def __eq__(self, other):
        return self.equals(other)

    def to_list(self):
        ' helper '
        return [self.get(i) for i in range(self.len())]

    def from_list(self, state):
        ' helper '
        [self.set(i, v) for i, v in enumerate(state)]


def dealloc_basestate(s):
    lib.BaseState__delete(s.c_base_state)
    s.c_base_state = None


###############################################################################

class LegalState:
    def __init__(self, c_legal_state):
        self.c_legal_state = c_legal_state

    def get_count(self):
        return lib.LegalState__getCount(self.c_legal_state)

    def get_legal(self, index):
        return lib.LegalState__getLegal(self.c_legal_state, index)

    def to_list(self):
        ' helper '
        return [self.get_legal(i) for i in range(self.get_count())]


###############################################################################

class JointMove:
    def __init__(self, c_joint_move):
        self.c_joint_move = c_joint_move

    def get(self, role_index):
        return lib.JointMove__get(self.c_joint_move, role_index)

    def set(self, role_index, value):
        lib.JointMove__set(self.c_joint_move, role_index, value)


def dealloc_jointmove(joint_move):
    lib.JointMove__delete(joint_move.c_joint_move)
    joint_move.c_joint_move = None


###############################################################################

class StateMachine:
    def __init__(self, c_statemachine, roles):
        self.c_statemachine = c_statemachine
        self._roles = roles

        # initial state has to be set here on c_statemachine
        self.reset()

    def get_roles(self):
        return self._roles

    def dupe(self):
        new_c_statemachine = lib.StateMachine__dupe(self.c_statemachine)
        return StateMachine(new_c_statemachine, self._roles)

    def get_initial_state(self):
        bs = self.new_base_state()
        lib.StateMachine__getInitialState(self.c_statemachine, bs.c_base_state)
        return bs

    def new_base_state(self):
        return BaseState(lib.StateMachine__newBaseState(self.c_statemachine))

    def update_bases(self, base_state):
        lib.StateMachine__updateBases(self.c_statemachine, base_state.c_base_state)

    def get_legal_state(self, role_index):
        return LegalState(lib.StateMachine__getLegalState(self.c_statemachine, role_index))

    def get_gdl(self, index):
        c_charstar = lib.StateMachine__getGDL(self.c_statemachine, index)
        return ffi.string(c_charstar)

    def legal_to_move(self, role_index, choice):
        c_charstar = lib.StateMachine__legalToMove(self.c_statemachine, role_index, choice)
        return ffi.string(c_charstar)

    def is_terminal(self):
        return lib.StateMachine__isTerminal(self.c_statemachine)

    def next_state(self, move, base_state):
        return lib.StateMachine__nextState(self.c_statemachine, move.c_joint_move, base_state.c_base_state)

    def get_joint_move(self):
        return JointMove(lib.StateMachine__getJointMove(self.c_statemachine))

    def reset(self):
        lib.StateMachine__reset(self.c_statemachine)

    def get_goal_value(self, role_index):
        return lib.StateMachine__getGoalValue(self.c_statemachine, role_index)

    def get_current_state(self, bs=None):
        if bs is None:
            bs = self.new_base_state()
        lib.StateMachine__getCurrentState(self.c_statemachine, bs.c_base_state)
        return bs

    def basestate_to_str(self, bs):
        ' helper '
        return " ".join([self.get_gdl(i) for i in range(bs.len()) if bs.get(i)])


###############################################################################

def create_statemachine(buf, roles):
    c_statemachine = lib.createStateMachineFromJSON(buf, len(buf))
    return StateMachine(c_statemachine, roles)


def create_goalless_statemachine(buf, roles):
    c_statemachine = lib.createGoallessStateMachineFromJSON(buf, len(buf))
    return StateMachine(c_statemachine, roles)


def create_combined_statemachine(buf, roles):
    c_statemachine = lib.createCombinedStateMachineFromJSON(buf, len(buf))
    return StateMachine(c_statemachine, roles)


def dealloc_statemachine(sm):
    ' called to explicitly delete the underlying statemachine '
    lib.StateMachine__delete(sm.c_statemachine)
    sm.c_statemachine = None


###############################################################################

class CppPlayerWrapper:
    def __init__(self, c_player):
        self.c_player = c_player
        log.info("creating CppPlayerWrapepr with %s" % self.c_player)

    def cleanup(self):
        lib.PlayerBase__cleanup(self.c_player)

    def on_meta_gaming(self, finish_time):
        lib.PlayerBase__onMetaGaming(self.c_player, finish_time)

    def before_apply_info(self):
        c_charstar = lib.PlayerBase__beforeApplyInfo(self.c_player)
        return ffi.string(c_charstar)

    def on_apply_move(self, move):
        lib.PlayerBase__onApplyMove(self.c_player, move.c_joint_move)

    def on_next_move(self, finish_time):
        return lib.PlayerBase__onNextMove(self.c_player, finish_time)


###############################################################################
# separate function to create player (since will different configuration for each player type)
###############################################################################

# IMPORTANT these players consume the statemachine sm.  It MUST not be cleaned up by the client.

def create_random_player(sm, our_role_index):
    return CppPlayerWrapper(lib.Player__createRandomPlayer(sm.c_statemachine, our_role_index))


def create_legal_player(sm, our_role_index):
    return CppPlayerWrapper(lib.Player__createLegalPlayer(sm.c_statemachine, our_role_index))


def create_simple_mcts_player(sm, our_role_index, *args):
    return CppPlayerWrapper(lib.Player__createSimpleMCTSPlayer(sm.c_statemachine, our_role_index, *args))


###############################################################################

class Logging:
    def verbose(self, msg):
        lib.Log_verbose(msg)

    def debug(self, msg):
        lib.Log_debug(msg)

    def info(self, msg):
        lib.Log_info(msg)

    def warning(self, msg):
        lib.Log_warning(msg)

    def error(self, msg):
        lib.Log_error(msg)

    def critical(self, msg):
        lib.Log_critical(msg)


###############################################################################

def depth_charge(sm, seconds):
    c_obj = lib.DepthChargeTest__create(sm.c_statemachine)
    lib.DepthChargeTest__doRollouts(c_obj, seconds)
    msecs = lib.DepthChargeTest__getResult(c_obj, 0)
    rollouts = lib.DepthChargeTest__getResult(c_obj, 1)
    num_state_changes = lib.DepthChargeTest__getResult(c_obj, 2)

    lib.DepthChargeTest__delete(c_obj)

    return msecs, rollouts, num_state_changes


###############################################################################

def initialise_k273(log_level, log_name_base="logfile"):
    count = 1
    while True:
        log_filename = "%s%03d.log" % (log_name_base, count)
        if not os.path.exists(log_filename):
            break

        count += 1

    lib.initK273(log_level, log_filename)
