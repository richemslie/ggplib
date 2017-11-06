#include "interface.h"

// example players
#include "example_players/simplemcts.h"
#include "example_players/legalplayer.h"
#include "example_players/randomplayer.h"

#include "player/player.h"

#include "perf_test.h"

#include "statemachine/goalless_sm.h"
#include "statemachine/combined.h"
#include "statemachine/statemachine.h"
#include "statemachine/propagate.h"
#include "statemachine/legalstate.h"

#include "statemachine/jointmove.h"

#include <k273/logging.h>
#include <k273/exception.h>

bool k273_initialised = false;

void initK273(int console, const char* filename) {
    if (k273_initialised) {
        return;
    }

    K273::loggerSetup(filename, K273::Logger::LOG_VERBOSE);

    k273_initialised = true;
}

// basestate

int BaseState__get(void* _bs, int index) {
    GGPLib::BaseState* bs = static_cast<GGPLib::BaseState*> (_bs);
    return bs->get(index);
}

void BaseState__set(void* _bs, int index, int value) {
    GGPLib::BaseState* bs = static_cast<GGPLib::BaseState*> (_bs);
    return bs->set(index, value);
}

long BaseState__hashCode(void* _bs) {
    GGPLib::BaseState* bs = static_cast<GGPLib::BaseState*> (_bs);
    return bs->hashCode();
}

int BaseState__equals(void* _bs, void* _other) {
    GGPLib::BaseState* bs = static_cast<GGPLib::BaseState*> (_bs);
    GGPLib::BaseState* other = static_cast<GGPLib::BaseState*>  (_other);
    return bs->equals(other);
}

void BaseState__assign(void* _bs, void* _from) {
    GGPLib::BaseState* bs = static_cast<GGPLib::BaseState*> (_bs);
    GGPLib::BaseState* from = static_cast<GGPLib::BaseState*> (_from);
    bs->assign(from);
}

void BaseState__deleteBaseState(void* _bs) {
    GGPLib::BaseState* bs = static_cast<GGPLib::BaseState*> (_bs);
    ::free(bs);
}

// Create a state machine
void* createStateMachine(int role_count, int num_bases, int num_transitions, int num_components, int num_ouputs, int topological_size) {
    GGPLib::StateMachineInterface* sm = new GGPLib::StateMachine(role_count, num_bases, num_transitions, num_components, num_ouputs, topological_size);
    return (void *) sm;
}

// Create a goalless state machine
void* createGoallessStateMachine(int role_count, void* _sm1, void* _sm2) {
    GGPLib::StateMachine* sm1 = static_cast<GGPLib::StateMachine*> (_sm1);
    GGPLib::StateMachine* sm2 = static_cast<GGPLib::StateMachine*> (_sm2);

    GGPLib::StateMachineInterface* sm = new GGPLib::GoalLessStateMachine(role_count, sm1, sm2);
    return (void *) sm;
}

void StateMachine__setRole(void* _sm, int role_index, const char* name, int input_start_index, int legal_start_index, int goal_start_index, int num_inputs_legals, int num_goals) {
    GGPLib::StateMachine* sm = static_cast<GGPLib::StateMachine*> (_sm);
    sm->setRole(role_index, name, input_start_index, legal_start_index, goal_start_index, num_inputs_legals, num_goals);
}

void StateMachine__setComponent(void* _sm, int component_id, int required_count_false, int required_count_true,
                                int output_index, int number_outputs, int initial_count, int incr, int topological_order) {
    GGPLib::StateMachine* sm = static_cast<GGPLib::StateMachine*> (_sm);
    sm->setComponent(component_id, required_count_false, required_count_true, output_index, number_outputs, initial_count, incr, topological_order);
}


void StateMachine__setOutput(void* _sm, int output_index, int component_id) {
    GGPLib::StateMachine* sm = static_cast<GGPLib::StateMachine*> (_sm);
    sm->setOutput(output_index, component_id);
}

void StateMachine__recordFinalise(void* _sm, int control_flows, int terminal_index) {
    try {
        GGPLib::StateMachine* sm = static_cast<GGPLib::StateMachine*> (_sm);
        sm->recordFinalise(control_flows, terminal_index);
    } catch (const K273::Assertion &exc) {
        fprintf(stderr, "Assertion : %s\n", exc.getMessage().c_str());
        fprintf(stderr, "Stacktrace :\n%s\n", exc.getStacktrace().c_str());
    }
}

void StateMachine__setMetaComponent(void* _sm, int component_id, const char* component_type, const char* gdl, const char* move, int goal_value) {
    GGPLib::StateMachine* sm = static_cast<GGPLib::StateMachine*> (_sm);
    sm->setMetaInformation(component_id, component_type, gdl, move, goal_value);
}

void StateMachine__setInitialState(void* _sm, void* _bs) {
    GGPLib::StateMachineInterface* sm = static_cast<GGPLib::StateMachineInterface*> (_sm);
    GGPLib::BaseState* bs = static_cast<GGPLib::BaseState*> (_bs);

    sm->setInitialState(bs);
}

void* StateMachine__newBaseState(void* _sm) {
    GGPLib::StateMachineInterface* sm = static_cast<GGPLib::StateMachineInterface*> (_sm);
    return (void *) sm->newBaseState();
}

void StateMachine__updateBases(void* _sm, void* _bs) {
    GGPLib::StateMachineInterface* sm = static_cast<GGPLib::StateMachineInterface*> (_sm);
    GGPLib::BaseState* bs = static_cast<GGPLib::BaseState*> (_bs);
    sm->updateBases(bs);
}

void* StateMachine__getLegalState(void* _sm, int role_index) {
    GGPLib::StateMachineInterface* sm = static_cast<GGPLib::StateMachineInterface*> (_sm);
    return (void *) sm->getLegalState(role_index);
}

const char* StateMachine__legalToMove(void* _sm, int role_index, int choice) {
    GGPLib::StateMachineInterface* sm = static_cast<GGPLib::StateMachineInterface*> (_sm);
    return sm->legalToMove(role_index, choice);
}

void* StateMachine__getJointMove(void* _sm) {
    GGPLib::StateMachineInterface* sm = static_cast<GGPLib::StateMachineInterface*> (_sm);
    return (void *) sm->getJointMove();
}

int StateMachine__isTerminal(void* _sm) {
    GGPLib::StateMachineInterface* sm = static_cast<GGPLib::StateMachineInterface*> (_sm);
    return sm->isTerminal();
}

void StateMachine__nextState(void* _sm, void* _move, void* _bs) {
    GGPLib::StateMachineInterface* sm = static_cast<GGPLib::StateMachineInterface*> (_sm);
    GGPLib::JointMove* joint_move = static_cast<GGPLib::JointMove*> (_move);
    GGPLib::BaseState* bs = static_cast<GGPLib::BaseState*> (_bs);
    sm->nextState(joint_move, bs);
}

int StateMachine__getGoalValue(void* _sm, int role_index) {
    GGPLib::StateMachineInterface* sm = static_cast<GGPLib::StateMachineInterface*> (_sm);
    return sm->getGoalValue(role_index);
}

void StateMachine__getCurrentState(void* _sm, void* _bs) {
    GGPLib::StateMachineInterface* sm = static_cast<GGPLib::StateMachineInterface*> (_sm);
    GGPLib::BaseState* bs = static_cast<GGPLib::BaseState*> (_bs);

    const GGPLib::BaseState* current_state = sm->getCurrentState();
    bs->assign(current_state);
}

void StateMachine__reset(void* _sm) {
    GGPLib::StateMachineInterface* sm = static_cast<GGPLib::StateMachineInterface*> (_sm);
    sm->reset();
}

int LegalState__getCount(void* _ls) {
    GGPLib::LegalState* legal_state = static_cast<GGPLib::LegalState*> (_ls);
    return legal_state->getCount();
}

int LegalState__getLegal(void* _ls, int index) {
    GGPLib::LegalState* legal_state = static_cast<GGPLib::LegalState*> (_ls);
    return legal_state->getLegal(index);
}

int JointMove__get(void* _move, int role_index) {
    GGPLib::JointMove* joint_move = static_cast<GGPLib::JointMove*> (_move);
    return joint_move->get(role_index);
}

void JointMove__set(void* _move, int role_index, int value) {
    GGPLib::JointMove* joint_move = static_cast<GGPLib::JointMove*> (_move);
    joint_move->set(role_index, value);
}

///////////////////////////////////////////////////////////////////////////////

void* createCombinedStateMachine(int role_count) {
    GGPLib::CombinedStateMachine* combined = new GGPLib::CombinedStateMachine(role_count);
    return (void *) combined;
}

void CombinedStateMachine__setGoalStateMachine(void* _combined, void* _sm) {
    GGPLib::CombinedStateMachine* combined = static_cast<GGPLib::CombinedStateMachine*> (_combined);
    GGPLib::StateMachine* sm = static_cast<GGPLib::StateMachine*> (_sm);
    combined->setGoalStateMachine(sm);
}

void CombinedStateMachine__setControlStateMachine(void* _combined, int control_index, int control_cid, void* _sm) {
    GGPLib::CombinedStateMachine* combined = static_cast<GGPLib::CombinedStateMachine*> (_combined);
    GGPLib::StateMachine* sm = static_cast<GGPLib::StateMachine*> (_sm);
    combined->setControlStateMachine(control_index, control_cid, sm);
}

///////////////////////////////////////////////////////////////////////////////

void* Player__createRandomPlayer(void* _sm, int our_role_index) {
    GGPLib::StateMachineInterface* sm = static_cast<GGPLib::StateMachine*> (_sm);
    GGPLib::PlayerBase* player = new RandomPlayer::Player(sm, our_role_index);
    return (void *) player;
}

void* Player__createLegalPlayer(void* _sm, int our_role_index) {
    GGPLib::StateMachineInterface* sm = static_cast<GGPLib::StateMachine*> (_sm);
    GGPLib::PlayerBase* player = new LegalPlayer::Player(sm, our_role_index);
    return (void *) player;
}

void* Player__createSimpleMCTSPlayer(void* _sm, int our_role_index,
                                     int skip_single_moves,
                                     double max_tree_search_time,
                                     long max_memory,
                                     long max_tree_playout_iterations,
                                     int max_number_of_nodes,
                                     double ucb_constant,
                                     int select_random_move_count,
                                     int dump_depth,
                                     double next_time) {

    GGPLib::SimpleMcts::Config* config = new GGPLib::SimpleMcts::Config;
    config->skip_single_moves = (bool) skip_single_moves;
    config->max_tree_search_time = max_tree_search_time;
    config->max_memory = max_memory;
    config->max_tree_playout_iterations = max_tree_playout_iterations;
    config->max_number_of_nodes = max_number_of_nodes;
    config->ucb_constant = ucb_constant;
    config->select_random_move_count = select_random_move_count;
    config->dump_depth = dump_depth;
    config->next_time = next_time;

    GGPLib::StateMachineInterface* sm = static_cast<GGPLib::StateMachine*> (_sm);
    GGPLib::PlayerBase* player = new GGPLib::SimpleMcts::Player(sm, our_role_index, config);
    return (void *) player;
}

void PlayerBase__cleanup(void* _player) {
    GGPLib::PlayerBase* player = static_cast<GGPLib::PlayerBase*> (_player);
    delete player;
}

void PlayerBase__onMetaGaming(void* _player, double end_time) {
    try {
        GGPLib::PlayerBase* player = static_cast<GGPLib::PlayerBase*> (_player);
        player->onMetaGaming(end_time);
    } catch (const K273::Exception &exc) {
        K273::l_critical("PlayerBase__onMetaGaming");
        K273::l_critical("Assertion : %s", exc.getMessage().c_str());
        K273::l_critical("Stacktrace : \n%s", exc.getStacktrace().c_str());
    } catch (...) {
        K273::l_critical("Assertion : x");
        K273::l_critical("Stacktrace : x");
    }
}

void PlayerBase__onApplyMove(void* _player, void* _move) {
    try {
        GGPLib::PlayerBase* player = static_cast<GGPLib::PlayerBase*> (_player);
        GGPLib::JointMove* joint_move = static_cast<GGPLib::JointMove*> (_move);
        player->onApplyMove(joint_move);
    } catch (const K273::Exception &exc) {
        K273::l_critical("PlayerBase__onApplyMove");
        K273::l_critical("Assertion : %s", exc.getMessage().c_str());
        K273::l_critical("Stacktrace :\n%s", exc.getStacktrace().c_str());
    } catch (...) {
        K273::l_critical("Assertion : x");
        K273::l_critical("Stacktrace : x");
    }
}

int PlayerBase__onNextMove(void* _player, double end_time) {
    try {
        GGPLib::PlayerBase* player = static_cast<GGPLib::PlayerBase*> (_player);
        return player->onNextMove(end_time);
    } catch (const K273::Exception &exc) {
        K273::l_critical("PlayerBase__onNextMove");
        K273::l_critical("Assertion : %s", exc.getMessage().c_str());
        K273::l_critical("Stacktrace : \n%s", exc.getStacktrace().c_str());
    } catch (...) {
        K273::l_critical("Assertion : x");
        K273::l_critical("Stacktrace : x");
    }

    return -1;
}

void* DepthChargeTest__create(void* _sm) {
    GGPLib::StateMachine* sm = static_cast<GGPLib::StateMachine*> (_sm);
    GGPLib::DepthChargeTest* dct = new GGPLib::DepthChargeTest(sm);
    return (void *) dct;
}

void DepthChargeTest__doRollouts(void* _dct, int seconds) {
    GGPLib::DepthChargeTest* dct = static_cast<GGPLib::DepthChargeTest*> (_dct);
    return dct->doRollouts(seconds);
}

int DepthChargeTest__getResult(void* _dct, int index) {
    GGPLib::DepthChargeTest* dct = static_cast<GGPLib::DepthChargeTest*> (_dct);
    return dct->getResult(index);
}

void DepthChargeTest__delete(void* _dct) {
    GGPLib::DepthChargeTest* dct = static_cast<GGPLib::DepthChargeTest*> (_dct);
    delete dct;
}

void Log_verbose(const char* msg) {
    K273::l_verbose("%s", msg);
}

void Log_debug(const char* msg) {
    K273::l_debug("%s", msg);
}

void Log_info(const char* msg) {
    K273::l_info("%s", msg);
}

void Log_warning(const char* msg) {
    K273::l_warning("%s", msg);
}

void Log_error(const char* msg) {
    K273::l_error("%s", msg);
}

void Log_critical(const char* msg) {
    K273::l_critical("%s", msg);
}
