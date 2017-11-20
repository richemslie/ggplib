#include "player/rollout.h"

#include <k273/logging.h>
#include <k273/exception.h>

using namespace K273;
using namespace GGPLib;

#define round_up_4(x) ((((x) / 4) + 1) * 4)

///////////////////////////////////////////////////////////////////////////////

RolloutBase::RolloutBase(StateMachineInterface* sm) :
    sm(sm),
    depth(0) {
    this->sm->getRoleCount();

    this->sm->reset();
    const BaseState* bs = this->sm->getCurrentState();

    this->initial_state = this->sm->newBaseState();
    this->joint_move_size = round_up_4(JointMove::mallocSize(this->sm->getRoleCount()));
    this->basestate_size = round_up_4(sizeof(BaseState) + bs->byte_count);

    this->moves = (char*) malloc(this->joint_move_size * RolloutBase::MAX_NUMBER_STATES);
    this->states = (char*) malloc(this->basestate_size * RolloutBase::MAX_NUMBER_STATES);

    for (int ii=0; ii<RolloutBase::MAX_NUMBER_STATES; ii++) {
        JointMove* move = reinterpret_cast<JointMove*> (this->moves + (ii * this->joint_move_size));
        move->setSize(this->sm->getRoleCount());
        BaseState* b = reinterpret_cast<BaseState*> (this->states + (ii * this->basestate_size));
        b->init(bs->size);
    }

    this->scores.reserve(sm->getRoleCount());
}

#undef round_up_4

RolloutBase::~RolloutBase() {
    K273::l_info("Destructing RolloutBase");
    free(this->initial_state);
    free(this->moves);
    free(this->states);

    // delete the statemachine
    delete this->sm;
    K273::l_info("Done destructing RolloutBase");
}

///////////////////////////////////////////////////////////////////////////////

void DepthChargeRollout::doRollout(const BaseState* start_state, int game_depth) {
    // game_depth not used

    this->initial_state->assign(start_state);
    this->sm->updateBases(this->initial_state);
    ASSERT (!this->sm->isTerminal());

    this->depth = 0;
    while (true) {
        ASSERT (this->depth < RolloutBase::MAX_NUMBER_STATES);

        if (this->sm->isTerminal()) {
            break;
        }

        JointMove* joint_move = this->getMove(this->depth);
        BaseState* next_state = this->getBaseState(this->depth);

        for (int ii=0; ii<this->sm->getRoleCount(); ii++) {
            const LegalState* ls = this->sm->getLegalState(ii);
            int x = this->random.getWithMax(ls->getCount());
            int choice = ls->getLegal(x);
            joint_move->set(ii, choice);
        }

        this->sm->nextState(joint_move, next_state);
        this->sm->updateBases(next_state);

        this->depth++;
    }

    this->scores.clear();
    for (int ii=0; ii<this->sm->getRoleCount(); ii++) {
        this->scores.emplace_back(this->sm->getGoalValue(ii));
    }
}
