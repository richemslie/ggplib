#pragma once

#include "statemachine/basestate.h"
#include "statemachine/legalstate.h"
#include "statemachine/jointmove.h"

#include "statemachine/statemachine.h"
#include "statemachine/propagate.h"

#include <k273/logging.h>

namespace GGPLib {
    class GoalLessStateMachine : public StateMachineInterface {
    public:
        GoalLessStateMachine(int role_count, StateMachine* goalless_sm, StateMachine* goal_sm) :
            role_count(role_count),
            goalless_sm(goalless_sm),
            goal_sm(goal_sm) {
        }

        virtual ~GoalLessStateMachine() {
            delete this->goal_sm;
            delete this->goalless_sm;
        }

    public:
        StateMachineInterface* dupe() const {
            K273::l_debug("Duping GoalLessStateMachine");
            return new GoalLessStateMachine(this->role_count,
                                            static_cast<StateMachine*> (this->goalless_sm->dupe()),
                                            static_cast<StateMachine*> (this->goal_sm->dupe()));
        }

    public:
        BaseState* newBaseState() const {
            return this->goalless_sm->newBaseState();
        }
        const BaseState* getCurrentState() const {
            return this->goalless_sm->getCurrentState();
        }

        void setInitialState(const BaseState* bs) {
            this->goalless_sm->setInitialState(bs);
        }

        void updateBases(const BaseState* bs) {
            this->goalless_sm->updateBases(bs);
        }

        LegalState* getLegalState(int role_index) {
            return this->goalless_sm->getLegalState(role_index);
        }

        const char* getStateString(int index) const {
            return this->goalless_sm->getStateString(index);
        }

        const char* legalToMove(int role_index, int choice) const {
            return this->goalless_sm->legalToMove(role_index, choice);
        }

        JointMove* getJointMove() {
            return this->goalless_sm->getJointMove();
        }

        bool isTerminal() const {
            return this->goalless_sm->isTerminal();
        }

        void nextState(const JointMove* move, BaseState* bs) {
            this->goalless_sm->nextState(move, bs);
        }

        int getGoalValue(int role_index) {
            // make goal sm have same state as goalless one
            this->goal_sm->updateBases(this->goalless_sm->getCurrentState());
            return this->goal_sm->getGoalValue(role_index);
        }

        void reset() {
            this->goalless_sm->reset();
        }

        int getRoleCount() const {
            return this->role_count;
        }

        const RoleInfo* getRoleInfo(int role_index) const {
            return this->goalless_sm->getRoleInfo(role_index);
        }

    private:
        const int role_count;
        StateMachine* goalless_sm;
        StateMachine* goal_sm;
    };
}
