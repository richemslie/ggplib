#pragma once

#include "statemachine/statemachine.h"
#include "statemachine/basestate.h"
#include "statemachine/legalstate.h"
#include "statemachine/jointmove.h"

#include <k273/util.h>

namespace GGPLib {

    class RolloutBase {
    public:
        RolloutBase(StateMachineInterface* sm);
        virtual ~RolloutBase();

    public:
        virtual void doRollout(const BaseState* start_state, int game_depth) = 0;

    public:
        // public interface
        int getScore(const int index) const {
            return this->scores[index];
        }

        const int getDepth() const {
            return this->depth;
        }

        const JointMove* getMove(int index) const {
            return reinterpret_cast <JointMove*> (this->moves + (index * this->joint_move_size));
        }

        const BaseState* getBaseState(int index) const {
            return reinterpret_cast <BaseState*> (this->states + (index * this->basestate_size));
        }

        const BaseState* getFinalBaseState() const {
            int idx = std::max(0, this->depth - 1);
            return this->getBaseState(idx);
        }

    protected:
        JointMove* getMove(int index) {
            return reinterpret_cast <JointMove*> (this->moves + (index * this->joint_move_size));
        }

        BaseState* getBaseState(int index) {
            return reinterpret_cast <BaseState*> (this->states + (index * this->basestate_size));
        }

    protected:
        StateMachineInterface* sm;
        BaseState* initial_state;

        int joint_move_size;
        int basestate_size;
        char* moves;
        char* states;
        int depth;

        std::vector <int> scores;
        K273::Random random;

    public:
        static const int MAX_NUMBER_STATES = 500;
    };


    class DepthChargeRollout : public RolloutBase {
    public:
        DepthChargeRollout(StateMachineInterface* sm) :
            RolloutBase(sm) {
        }

        virtual ~DepthChargeRollout() {
        }

    public:
        void doRollout(const BaseState* start_state, int game_depth);
    };

}

