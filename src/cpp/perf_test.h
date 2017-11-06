#pragma once

#include "statemachine/statemachine.h"
#include "statemachine/basestate.h"
#include "statemachine/legalstate.h"
#include "statemachine/jointmove.h"

#include <k273/util.h>

namespace GGPLib {

    class DepthChargeTest {
    public:
        DepthChargeTest(StateMachineInterface* sm) :
            sm(sm),
            msecs_taken(0),
            rollouts(0),
            num_state_changes(0) {

            this->joint_move = this->sm->getJointMove();
            this->next_state = this->sm->newBaseState();
        }

        ~DepthChargeTest() {
            free (this->joint_move);
            free (this->next_state);
        }

    public:
        void doRollouts(int second);

        int getResult(int index) {
            if (index == 0) {
                return this->msecs_taken;
            }

            if (index == 1) {
                return this->rollouts;
            }

            if (index == 2) {
                return this->num_state_changes;
            }

            return -1;
        }

    private:
        StateMachineInterface* sm;
        JointMove* joint_move;
        BaseState* next_state;

        int msecs_taken;
        int rollouts;
        int num_state_changes;

        K273::Random random;
    };
}
