#pragma once

#include "statemachine/statemachine.h"
#include "statemachine/basestate.h"
#include "statemachine/legalstate.h"
#include "statemachine/metainfo.h"
#include "statemachine/roleinfo.h"
#include "statemachine/jointmove.h"

#include <k273/util.h>
#include <k273/exception.h>

namespace GGPLib {
    enum Instruction : uint8_t {
            SAME_N = 0,
            TRIGGER_LEGAL = 1,
            TRIGGER_TRANSITION = 2,
            INVERT_N = 3,
            NOUGHT = 4,
            };

    struct Component {
        // used propagate legal
        uint8_t role_index;

        Instruction instruction;
        uint16_t count;

        uint32_t output_index;
    };

    class StateMachine : public StateMachineInterface {
    public:
        StateMachine(int role_count, int num_bases, int num_transitions,
                     int num_components, int num_outputs, int topological_size);
        virtual ~StateMachine();

    public:
        StateMachineInterface* dupe() const;

    public:
        // this is factory/build stuff:

        void setRole(int role_index, const char* name, int input_start_index, int legal_start_index, int goal_start_index, int num_inputs_legals, int num_goals);
        void setComponent(int component_id, int required_count_false, int required_count_true,
                          int output_index, int number_outputs, int initial_count, int incr, int topological_order);
        void setOutput(int output_index, int component_id);
        void recordFinalise(int control_flows, int terminal_index);

        void setMetaInformation(int component_id, const std::string& component_type,
                                const std::string& gdl, const std::string& move, int goal_value);

    public:
        // this is the interface implementation:

        BaseState* newBaseState() const;
        const BaseState* getCurrentState() const;

        void setInitialState(const BaseState* bs);
        const BaseState* getInitialState() const;

        void updateBases(const BaseState* bs);
        LegalState* getLegalState(int role_index);

        const char* getGDL(int index) const;
        const char* legalToMove(int role_index, int choice) const;

        JointMove* getJointMove();
        bool isTerminal() const;
        void nextState(const JointMove* move, BaseState* bs);
        int getGoalValue(int role_index);

        void reset();
        int getRoleCount() const {
            return this->role_count;
        }

        const RoleInfo* getRoleInfo(int role_index) const {
            return &this->roles[role_index];
        }

    private:
        void propagate(Component* component, bool value) {
           Component** pt_output = this->component_outputs + component->output_index;
           if (value) {
               this->forwardPropagateValueP(pt_output);
           } else {
               this->forwardPropagateValueN(pt_output);
           }
        }

        void forwardPropagateValueP1(Component** pt_output) {
            // CONSTRAINT: only called if propagation is required
            Component* component = *pt_output;
            component->count++;
            if (unlikely(component->count == 0)) {
                switch (component->instruction) {
                case Instruction::SAME_N:
                    this->forwardPropagateValueP(this->component_outputs + component->output_index);
                    break;
                case Instruction::TRIGGER_LEGAL:
                    this->triggerPropagateLegalP(component);
                    break;
                case Instruction::TRIGGER_TRANSITION:
                    this->triggerPropagateTransitionP(component);
                    break;
                case Instruction::INVERT_N:
                    this->forwardPropagateValueN(this->component_outputs + component->output_index);
                    break;
                default:
                    break;
                }
            }
        }

        void forwardPropagateValueN1(Component** pt_output) {
            // CONSTRAINT: only called if propagation is required
            Component* component = *pt_output;

            if (unlikely(component->count == 0)) {
                switch (component->instruction) {
                case Instruction::SAME_N:
                    this->forwardPropagateValueN(this->component_outputs + component->output_index);
                    break;
                case Instruction::TRIGGER_LEGAL:
                    this->triggerPropagateLegalN(component);
                    break;
                case Instruction::TRIGGER_TRANSITION:
                    this->triggerPropagateTransitionN(component);
                    break;
                case Instruction::INVERT_N:
                    this->forwardPropagateValueP(this->component_outputs + component->output_index);
                    break;
                default:
                    break;
                }
            }

            component->count--;
        }

        // important: DONT inline these
        void triggerPropagateLegalP(Component* component);
        void triggerPropagateLegalN(Component* component);
        void triggerPropagateTransitionP(Component* component);
        void triggerPropagateTransitionN(Component* component);

        void forwardPropagateValueP(Component** pt_output);
        void forwardPropagateValueN(Component** pt_output);

    private:
        const int role_count;
        const int num_bases;
        const int num_transitions;
        const int num_components;
        const int total_num_outputs;
        const int topological_size;

        bool initialised;

        BaseState* current_state;
        BaseState* initial_state;
        BaseState* transition_state;
        JointMove* preserve_last_move;

        int terminal_index;
        int transitions_index;

        // XXX test/replace this with a vector
        RoleInfo roles[MAX_NUMBER_PLAYERS];
        MetaComponentInfo* metas;

        Component* components;
        Component** component_outputs;
    };
}
