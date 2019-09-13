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

#include "external/draughts_desc.h"
#include "external/draughts_board.h"
#include "external/draughts_sm.h"

#include <k273/algo.h>
#include <k273/json.h>
#include <k273/logging.h>
#include <k273/exception.h>

#include <string>

bool k273_initialised = false;

void initK273(int console, const char* filename) {
    if (k273_initialised) {
        return;
    }

    K273::loggerSetup(filename, K273::Logger::LOG_VERBOSE);

    k273_initialised = true;
}

static void logExceptionWrapper(const std::string& name) {
    try {
        K273::l_critical("an exception was thrown in in %s:", name.c_str());
        throw;

    } catch (const K273::Exception& exc) {
        K273::l_critical("K273::Exception Message : %s", exc.getMessage().c_str());
        K273::l_critical("K273::Exception Stacktrace : \n%s", exc.getStacktrace().c_str());

    } catch (std::exception& exc) {
        K273::l_critical("std::exception What : %s", exc.what());

    } catch (...) {
        K273::l_critical("Unknown exception");
    }
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

int BaseState__len(void* _bs) {
    GGPLib::BaseState* bs = static_cast<GGPLib::BaseState*> (_bs);
    return bs->size;
}

void BaseState__delete(void* _bs) {
    GGPLib::BaseState* bs = static_cast<GGPLib::BaseState*> (_bs);
    ::free(bs);
}

char* BaseState__raw(void* _bs) {
    GGPLib::BaseState* bs = static_cast<GGPLib::BaseState*> (_bs);
    uint8_t* buf = (uint8_t*) malloc(bs->byte_count);
    uint8_t* pt_bs_data = (uint8_t*) bs->data;
    for (int ii=0; ii<bs->byte_count; ii++) {
        buf[ii] = K273::reverseByte(pt_bs_data[ii]);
    }

    return (char *) buf;
}

int BaseState__rawBytes(void* _bs) {
    GGPLib::BaseState* bs = static_cast<GGPLib::BaseState*> (_bs);
    return bs->byte_count;
}

void BaseState__setRaw(void* _bs, const char* buf) {
    GGPLib::BaseState* bs = static_cast<GGPLib::BaseState*> (_bs);

    uint8_t* pt_buf = (uint8_t*) buf;
    uint8_t* pt_bs_data = (uint8_t*) bs->data;
    for (int ii=0; ii<bs->byte_count; ii++) {
        pt_bs_data[ii] = K273::reverseByte(pt_buf[ii]);
    }
}

///////////////////////////////////////////////////////////////////////////////

void StateMachine__setInitialState(void* _sm, void* _bs) {
    GGPLib::StateMachineInterface* sm = static_cast<GGPLib::StateMachineInterface*> (_sm);
    GGPLib::BaseState* bs = static_cast<GGPLib::BaseState*> (_bs);

    sm->setInitialState(bs);
}

void* StateMachine__dupe(void* _sm) {
    GGPLib::StateMachine* sm = static_cast<GGPLib::StateMachine*> (_sm);
    return (void *) sm->dupe();
}

void StateMachine__delete(void* _sm) {
    GGPLib::StateMachine* sm = static_cast<GGPLib::StateMachine*> (_sm);
    delete sm;
}

///////////////////////////////////////////////////////////////////////////////

void* StateMachine__newBaseState(void* _sm) {
    GGPLib::StateMachineInterface* sm = static_cast<GGPLib::StateMachineInterface*> (_sm);
    return (void *) sm->newBaseState();
}

void StateMachine__getInitialState(void* _sm, void* _bs) {
    GGPLib::StateMachineInterface* sm = static_cast<GGPLib::StateMachineInterface*> (_sm);
    GGPLib::BaseState* bs = static_cast<GGPLib::BaseState*> (_bs);

    const GGPLib::BaseState* init_state = sm->getInitialState();
    bs->assign(init_state);
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

void JointMove__delete(void* _move) {
    GGPLib::JointMove* joint_move = static_cast<GGPLib::JointMove*> (_move);
    ::free(joint_move);
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
    } catch (...) {
        logExceptionWrapper(__PRETTY_FUNCTION__);
    }
}

const char* PlayerBase__beforeApplyInfo(void* _player) {
    // use static to keep memory around
    static std::string res;
    try {
        GGPLib::PlayerBase* player = static_cast<GGPLib::PlayerBase*> (_player);
        res = player->beforeApplyInfo();
        return res.c_str();

    } catch (...) {
        logExceptionWrapper(__PRETTY_FUNCTION__);
    }

    return "";
}

void PlayerBase__onApplyMove(void* _player, void* _move) {
    try {
        GGPLib::PlayerBase* player = static_cast<GGPLib::PlayerBase*> (_player);
        GGPLib::JointMove* joint_move = static_cast<GGPLib::JointMove*> (_move);
        player->onApplyMove(joint_move);
    } catch (...) {
        logExceptionWrapper(__PRETTY_FUNCTION__);
    }
}

int PlayerBase__onNextMove(void* _player, double end_time) {
    try {
        GGPLib::PlayerBase* player = static_cast<GGPLib::PlayerBase*> (_player);
        return player->onNextMove(end_time);
    } catch (...) {
        logExceptionWrapper(__PRETTY_FUNCTION__);
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

static GGPLib::StateMachine* createStateMachine(const K273::JsonValue root) {
    const K273::JsonValue d = root["create"];

    GGPLib::StateMachine* sm = new GGPLib::StateMachine(d["role_count"].asInt(),
                                                        d["num_bases"].asInt(),
                                                        d["num_transitions"].asInt(),
                                                        d["num_components"].asInt(),
                                                        d["num_outputs"].asInt(),
                                                        d["topological_size"].asInt());


    for (auto r : root["roles"]) {
        sm->setRole(r["role_index"].asInt(),
                    r["name"].asString().c_str(),
                    r["input_start_index"].asInt(),
                    r["legal_start_index"].asInt(),
                    r["goal_start_index"].asInt(),
                    r["num_inputs_legals"].asInt(),
                    r["num_goals"].asInt());
    }

    for (auto c : root["components"]) {
        sm->setComponent(c[0].asInt(), c[1].asInt(), c[2].asInt(), c[3].asInt(),
                         c[4].asInt(), c[5].asInt(), c[6].asInt(), c[7].asInt());
    }

    for (auto o : root["outputs"]) {
        sm->setOutput(o[0].asInt(), o[1].asInt());
    }

    for (auto m : root["metas"]) {
        sm->setMetaInformation(m["component_id"].asInt(),
                               m["typename"].asString(),
                               m["gdl_str"].asString(),
                               m["move"].asString(),
                               m["goal_value"].asInt());
    }

    K273::l_info("control_flows %d, terminal_index %d",
                 root["control_flows"].asInt(), root["terminal_index"].asInt());
    sm->recordFinalise(root["control_flows"].asInt(), root["terminal_index"].asInt());

    // initial_state
    GGPLib::BaseState* bs = sm->newBaseState();
    int index = 0;
    for (auto v : root["initial_state"]) {
        bs->set(index, v.asInt());
        index++;
    }

    sm->setInitialState(bs);
    sm->reset();
    K273::l_info("Built sm via JSON");

    return sm;
}

void* createStateMachineFromJSON(const char* msg, int size) {
    try {
        K273::JsonValue root = K273::JsonValue::parseJson(msg, size);
        GGPLib::StateMachineInterface* sm = ::createStateMachine(root);
        return (void *) sm;

    } catch (...) {
        logExceptionWrapper(__PRETTY_FUNCTION__);
    }

    return nullptr;
}

void* createGoallessStateMachineFromJSON(const char* msg, int size) {
    try {
        K273::JsonValue root = K273::JsonValue::parseJson(msg, size);
        int role_count = root["role_count"].asInt();
        GGPLib::StateMachine* goal_sm = ::createStateMachine(root["goal_sm"]);
        GGPLib::StateMachine* goalless_sm = ::createStateMachine(root["goalless_sm"]);

        GGPLib::StateMachineInterface* sm = new GGPLib::GoalLessStateMachine(role_count,
                                                                             goalless_sm,
                                                                             goal_sm);
        return (void *) sm;

    } catch (...) {
        logExceptionWrapper(__PRETTY_FUNCTION__);
    }

    return nullptr;
}


void* createCombinedStateMachineFromJSON(const char* msg, int size) {
    try {
        K273::JsonValue root = K273::JsonValue::parseJson(msg, size);
        GGPLib::StateMachine* goal_sm = ::createStateMachine(root["goal_sm"]);
        int number_control_states = root["num_controls"].asInt();

        GGPLib::CombinedStateMachine* combined = new GGPLib::CombinedStateMachine(number_control_states);
        combined->setGoalStateMachine(goal_sm);

        for (auto control_sm : root["control_sms"]) {
            GGPLib::StateMachine* sm = ::createStateMachine(control_sm);
            int idx = control_sm["idx"].asInt();
            int control_cid = control_sm["control_cid"].asInt();
            combined->setControlStateMachine(idx, control_cid, sm);
        }

        // has to be called after setting the controls
        combined->reset();

        GGPLib::StateMachineInterface* sm = combined;
        return (void *) sm;

    } catch (...) {
        logExceptionWrapper(__PRETTY_FUNCTION__);
    }

    return nullptr;
}

static GGPLib::StateMachineInterface* getSMDraughts(int size, bool breakthrough_mode, bool killer_mode) {
    K273::l_info("in getSMDraughts size: %d [%s;%s])", size,
                 breakthrough_mode ? "breakthrough_mode" : "",
                 killer_mode ? "killer_mode" : "");

    try {
        ASSERT(!(breakthrough_mode && killer_mode));

        InternationalDraughts::Description* desc = new InternationalDraughts::Description(size);
        InternationalDraughts::Board* board = new InternationalDraughts::Board(desc, breakthrough_mode, killer_mode);
        GGPLib::StateMachineInterface* sm = new InternationalDraughts::SM(board, desc);

        return sm;

    } catch (...) {
        logExceptionWrapper(__PRETTY_FUNCTION__);
    }

    return nullptr;
}

void* getSMDraughts_10x10() {
    return (void *) getSMDraughts(10, false, false);
}

void* getSMDraughtsKiller_10x10() {
    return (void *) getSMDraughts(10, false, true);
}

void* getSMDraughtsBreakthrough_10x10() {
    return (void *) getSMDraughts(10, true, false);
}
