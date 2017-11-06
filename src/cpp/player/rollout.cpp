#include "player/rollout.h"

#include <k273/exception.h>

using namespace K273;
using namespace GGPLib;

///////////////////////////////////////////////////////////////////////////////

void DepthChargeRollout::doRollout(const BaseState* start_state) {

    this->sm->updateBases(start_state);
    ASSERT (!this->sm->isTerminal());

    int depth = 0;

    const int role_count = this->sm->getRoleCount();
    while (true) {
        ASSERT (depth < DepthChargeRollout::MAX_NUMBER_SIM_STATES);

        if (this->sm->isTerminal()) {
            break;
        }

        // populate joint move
        for (int ii=0; ii<role_count; ii++) {
            const LegalState* ls = this->sm->getLegalState(ii);
            int x = this->random.getWithMax(ls->getCount());
            int choice = ls->getLegal(x);
            this->joint_move->set(ii, choice);
        }

        this->sm->nextState(this->joint_move, this->next_state);
        this->sm->updateBases(this->next_state);

        depth++;
    }

    this->scores.clear();
    for (int ii=0; ii<this->sm->getRoleCount(); ii++) {
        this->scores.emplace_back(this->sm->getGoalValue(ii));
    }
}

