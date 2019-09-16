// local includes
#include "sm.h"
#include "desc.h"
#include "board.h"

// k273 includes
#include <k273/logging.h>
#include <k273/exception.h>

// ggplib includes
#include <statemachine/jointmove.h>
#include <statemachine/legalstate.h>
#include <statemachine/basestate.h>


using namespace Baduk;

/*
- Have 2 boards: cur_board, update_board
- Have 2 basestates: cur_state, update_state
- All sm stuff on cur_state

  - except nextState()
     - if cur_state != update_state:
     - copy cur_state->update_state, sync update_board
     - modify in place the update_state
     - copy update_state to basestate passed in.

  - except updateBases()
     - check if state == either state and set that to cur_state/cur_board
     - otherwise sync to cur_state/cur_board
*/

///////////////////////////////////////////////////////////////////////////////

SM::SM(const Description* board_desc) :
    board_desc(board_desc),
    cur_board(new Board(board_desc)),
    update_board(new Board(board_desc)),
    update_board_set(false) {

    this->cur_state = this->newBaseState();
    this->update_state = this->newBaseState();
    this->initial_state = this->newBaseState();

    this->board_desc->setInitialState(this->initial_state);

    this->legal_states[0] = new GGPLib::LegalState(board_desc->legalsSize(Role::Black));
    this->legal_states[1] = new GGPLib::LegalState(board_desc->legalsSize(Role::White));

    // sm.reset() will be called in ggplib.interface.StateMachine()
}

SM::~SM() {
    K273::l_warning("In SM::~SM()");
    delete this->cur_board;
    delete this->update_board;

    // ZZZ XXX leaking tmp
    //delete (this->legal_states[0]);
    //delete (this->legal_states[1]);

    ::free(this->cur_state);
    ::free(this->update_state);
    ::free(this->initial_state);
}

GGPLib::StateMachineInterface* SM::dupe() const {
    SM* duped = new SM(this->board_desc);
    duped->cur_state->assign(this->cur_state);
    duped->updateBases(duped->cur_state);
    duped->reset();
    return duped;
}

void SM::reset() {
    this->updateBases(this->getInitialState());
}

void SM::updateBases(const GGPLib::BaseState* bs) {
    // XXX ZZZ switch to either board????
    if (this->update_board_set) {
    }

    this->cur_state->assign(bs);

    this->cur_board->setFromBS(this->cur_state);
    this->cur_board->moveGen(this->legal_states[0], this->legal_states[1]);
}

GGPLib::BaseState* SM::newBaseState() const {
    int num_bases = 4 * this->board_desc->numberPoints() + 5;

    void* mem = ::malloc(GGPLib::BaseState::mallocSize(num_bases));
    GGPLib::BaseState* bs = static_cast <GGPLib::BaseState*>(mem);
    bs->init(num_bases);
    return bs;
}

const GGPLib::BaseState* SM::getCurrentState() const {
    return this->cur_state;
}

void SM::setInitialState(const GGPLib::BaseState* bs) {
    ASSERT_MSG(false, "not supported");
}

const GGPLib::BaseState* SM::getInitialState() const {
    return this->initial_state;
}

GGPLib::LegalState* SM::getLegalState(int role_index) {
    return this->legal_states[role_index];
}

GGPLib::JointMove* SM::getJointMove() {
    // zero array size malloc
    void* mem = malloc(GGPLib::JointMove::mallocSize(this->getRoleCount()));
    GGPLib::JointMove* move = static_cast <GGPLib::JointMove*>(mem);
    move->setSize(this->getRoleCount());
    return move;
}

void SM::nextState(const GGPLib::JointMove* move, GGPLib::BaseState* bs) {
    this->update_state->assign(this->cur_state);
    this->update_board->setFromBS(this->update_state);
    this->update_board->playMove(move);
    this->update_board->setToBS(this->update_state);

    this->update_board_set = true;

    bs->assign(this->update_state);
}

const char* SM::legalToMove(int role_index, int choice) const {
    // get from board_desc (same for both bt/non bt variants)
    return this->board_desc->legalToMove(role_index, choice);
}

bool SM::isTerminal() const {
    return this->cur_board->finished();
}

int SM::getGoalValue(int role_index) {
    // undefined, call getGoalValue() in a non terminal state at your peril
    if (!this->isTerminal()) {
        return -1;
    }

    float white_score = this->actualScore();

    // ambiguous board, should never happen in terminal state (XXX assert)
    if (white_score < -1000) {
        return -1;
    }

    if (std::abs(white_score) < 0.0001) {
        return 50;
    }

    // white
    if (role_index == 1) {
        if (white_score > 0) {
            return 100;
        } else {
            return 0;
        }

    } else {
        if (white_score < 0) {
            return 100;
        } else {
            return 0;
        }
    }
}

int SM::getRoleCount() const {
    return 2;
}

float SM::actualScore() const {
    return this->cur_board->actualScore();
}
