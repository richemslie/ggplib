#pragma once

#include "statemachine/statemachine.h"
#include "statemachine/basestate.h"
#include "statemachine/legalstate.h"
#include "statemachine/jointmove.h"

#include <k273/util.h>

namespace GGPLib {

class DepthChargeRollout {
public:
    DepthChargeRollout(StateMachineInterface* sm) :
        sm(sm) {
        this->joint_move = this->sm->getJointMove();
        this->next_state = this->sm->newBaseState();
    }

    ~DepthChargeRollout() {
        free(this->joint_move);
        free(this->next_state);
    }

public:
    void doRollout(const BaseState* start_state);

    int getScore(const int index) const {
        return this->scores[index];
    }

private:
    StateMachineInterface* sm;
    JointMove* joint_move;
    BaseState* next_state;

    std::vector <int> scores;
    K273::Random random;

    static const int MAX_NUMBER_SIM_STATES = 500;
};

}

