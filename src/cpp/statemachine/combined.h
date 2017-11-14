#pragma once

#include "statemachine/basestate.h"
#include "statemachine/legalstate.h"
#include "statemachine/jointmove.h"

#include "statemachine/statemachine.h"
#include "statemachine/propagate.h"

#include <k273/exception.h>

namespace GGPLib {

    struct ControlInfo {
        int control_index;
        int control_cid;
        StateMachine* sm;
    };

    class CombinedStateMachine : public StateMachineInterface {
    public:
        CombinedStateMachine(int number_control_states);
        virtual ~CombinedStateMachine();

        void setGoalStateMachine(StateMachine* goal_sm);
        void setControlStateMachine(int control_index, int control_cid, StateMachine* control_sm);

    public:
        StateMachineInterface* dupe() const;

    public:
        BaseState* newBaseState() const {
            return this->current->newBaseState();
        }

        const BaseState* getCurrentState() const {
            return this->current->getCurrentState();
        }

        void setInitialState(const BaseState* bs) {
            ASSERT_MSG(false, "Should never be called");
        }

        void updateBases(const BaseState* bs) {
            this->current = this->getControl(bs)->sm;
            this->current->updateBases(bs);
        }

        LegalState* getLegalState(int role_index) {
            return this->current->getLegalState(role_index);
        }

        const char* getGDL(int index) const {
            return this->current->getGDL(index);
        }

        const char* legalToMove(int role_index, int choice) const {
            return this->current->legalToMove(role_index, choice);
        }

        JointMove* getJointMove() {
            return this->current->getJointMove();
        }

        bool isTerminal() const {
            return this->current->isTerminal();
        }

        void nextState(const JointMove* move, BaseState* bs) {
            this->current->nextState(move, bs);
        }

        int getGoalValue(int role_index) {
            if (this->goal_sm != nullptr) {
                // make goal sm have same state as goalless one
                this->goal_sm->updateBases(this->current->getCurrentState());
                return this->goal_sm->getGoalValue(role_index);
            } else {
                return this->current->getGoalValue(role_index);
            }
        }

        void reset();

        int getRoleCount() const {
            return this->goal_sm->getRoleCount();
        }

        const RoleInfo* getRoleInfo(int role_index) const {
            return this->current->getRoleInfo(role_index);
        }

    private:
        ControlInfo* getControl(const BaseState* bs);

    private:
        const int number_control_states;
        StateMachine* goal_sm;
        ControlInfo* controls;
        StateMachine* current;
    };

}
