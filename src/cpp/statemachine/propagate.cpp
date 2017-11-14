
#include "propagate.h"

#include "statemachine/basestate.h"
#include "statemachine/legalstate.h"
#include "statemachine/jointmove.h"
#include "statemachine/metainfo.h"
#include "statemachine/roleinfo.h"

#include <k273/logging.h>
#include <k273/exception.h>

using namespace std;
using namespace GGPLib;

///////////////////////////////////////////////////////////////////////////////

StateMachine::StateMachine(int role_count, int num_bases, int num_transitions,
                           int num_components, int total_num_outputs, int topological_size) :
    role_count(role_count),
    num_bases(num_bases),
    num_transitions(num_transitions),
    num_components(num_components),
    total_num_outputs(total_num_outputs),
    topological_size(topological_size),
    initialised(false) {

    // we can either have no transitions, or the same number as bases
    ASSERT (num_transitions == 0 || num_transitions == num_bases);

    this->components = new Component[num_components];
    this->component_outputs = new Component*[total_num_outputs];

    this->metas = new MetaComponentInfo[num_components];

    this->current_state = this->newBaseState();
    this->initial_state = this->newBaseState();
    this->transition_state = this->newBaseState();

    this->preserve_last_move = this->getJointMove();
}

StateMachine::~StateMachine() {
    K273::l_debug("Entering StateMachine::~StateMachine()");
    free(this->transition_state);
    free(this->initial_state);
    free(this->current_state);
    free(this->preserve_last_move);
    delete[] this->metas;
    delete[] this->component_outputs;
    delete[] this->components;
}

///////////////////////////////////////////////////////////////////////////////

StateMachineInterface* StateMachine::dupe() const {
    ASSERT (this->initialised);

    StateMachine* d = new StateMachine(this->role_count,
                                       this->num_bases,
                                       this->num_transitions,
                                       this->num_components,
                                       this->total_num_outputs,
                                       this->topological_size);

    d->current_state->assign(this->current_state);
    d->initial_state->assign(this->initial_state);
    d->transition_state->assign(this->transition_state);

    for (int ii=0; ii<this->role_count; ii++) {
        d->preserve_last_move->set(ii, this->preserve_last_move->get(ii));
    }

    d->terminal_index = this->terminal_index;
    d->transitions_index = this->transitions_index;

    // copy roles:
    for (int ii=0; ii<this->role_count; ii++) {
        RoleInfo* d_role_info = &d->roles[ii];
        const RoleInfo* this_role_info = &this->roles[ii];
        d_role_info->name = this_role_info->name;
        d_role_info->input_start_index = this_role_info->input_start_index;
        d_role_info->legal_start_index = this_role_info->legal_start_index;
        d_role_info->goal_start_index = this_role_info->goal_start_index;
        d_role_info->num_inputs_legals = this_role_info->num_inputs_legals;
        d_role_info->num_goals = this_role_info->num_goals;
        d_role_info->legal_state.resize(this_role_info->num_inputs_legals);

        // copy the legal state
        ASSERT (d_role_info->legal_state.getCount() == 0);
        for (int jj=0; jj<this_role_info->legal_state.getCount(); jj++) {
            d_role_info->legal_state.insert(this_role_info->legal_state.getLegal(jj));
        }
    }

    // copy metas:
    for (int ii=0; ii<this->num_components; ii++) {
        MetaComponentInfo* d_meta = d->metas + ii;
        const MetaComponentInfo* this_meta = this->metas + ii;

        d_meta->component_id = this_meta->component_id;
        d_meta->type = this_meta->type;
        d_meta->gdl = this_meta->gdl;
        d_meta->move = this_meta->move;
        d_meta->goal_value = this_meta->goal_value;
    }

    memcpy(d->components, this->components, sizeof(Component) * this->num_components);

    // copy the outputs...
    for (int ii=0; ii<this->total_num_outputs; ii++) {
        Component** d_output = d->component_outputs + ii;
        Component** this_output = this->component_outputs + ii;

        if (*this_output == nullptr) {
            *d_output = nullptr;
        } else {
            int component_id = *this_output - this->components;
            *d_output = d->components + component_id;
        }
    }

    d->initialised = true;
    K273::l_debug("Duped StateMachine with %d components", d->num_components);
    return d;
}

///////////////////////////////////////////////////////////////////////////////

void StateMachine::setRole(int role_index, const char* name, int input_start_index, int legal_start_index, int goal_start_index, int num_inputs_legals, int num_goals) {
    RoleInfo* role_info = &this->roles[role_index];
    role_info->name = name;
    role_info->input_start_index = input_start_index;
    role_info->legal_start_index = legal_start_index;
    role_info->goal_start_index = goal_start_index;
    role_info->num_inputs_legals = num_inputs_legals;
    role_info->num_goals = num_goals;

    role_info->legal_state.resize(num_inputs_legals);
}

void StateMachine::setComponent(int component_id, int required_count_false, int required_count_true,
                                int output_index, int number_outputs, int initial_count,
                                int incr, int topological_order) {
    //K273::l_info("setting component %d with output index %d and number_outputs %d init:%d incr: %d topological_order %d",
    //             component_id, output_index, number_outputs, initial_count, incr, topological_order);

    ASSERT (component_id < this->num_components);
    Component* component = this->components + component_id;
    ASSERT (sizeof(Component) == 8);
    memset(component, 0, sizeof(Component));

    // set 0 -> true
    component->count = ((uint16_t) initial_count) - ((uint16_t) required_count_true);

    if (number_outputs == 0) {
        component->instruction = NOUGHT;

    } else {
        if (incr > 0) {
            component->instruction = SAME_N;
        } else {
            component->instruction = INVERT_N;
        }
    }

    // role_index set later

    component->output_index = output_index;
}

void StateMachine::setOutput(int output_index, int component_id) {
    Component** output = this->component_outputs + output_index;
    ASSERT (component_id >= -1 && component_id < num_components);
    if (component_id == -1) {
        *output = nullptr;
    } else {
        *output = this->components + component_id;
    }
}

void StateMachine::recordFinalise(int control_flows, int terminal_index) {
    // ok all done.  check things are sane.

    /* order (indexed by topological order):
        0. bases propositions
        0. inputs propositions (by role)
        *. control flow
        *. terminal
        *. goals (by role)
       -2. transitions 9
       -1. legals (by role)
    */

    // base/inputs
    int total = this->num_bases;
    for (int ii=0; ii<this->role_count; ii++) {
        RoleInfo* role_info = &this->roles[ii];
        ASSERT (total == role_info->input_start_index);
        total += role_info->num_inputs_legals;
    }

    // control flow
    total += control_flows;

    // terminal
    this->terminal_index = terminal_index;
    ASSERT (total == this->terminal_index);
    total++;

    // goals
    for (int ii=0; ii<this->role_count; ii++) {
        // there may be no goals
        RoleInfo* role_info = &this->roles[ii];
        if (role_info->num_goals) {
            ASSERT (total == role_info->goal_start_index);
            total += role_info->num_goals;
        }
    }

    // transitions
    this->transitions_index = total;
    total += this->num_transitions;

    // legals
    for (int ii=0; ii<this->role_count; ii++) {
        // there may be no legals (we encode this with a minus 1, sort of a hack since we shared legals and inputs XXX
        // we ought to fix this)
        RoleInfo* role_info = &this->roles[ii];
        if (role_info->legal_start_index != -1) {
            ASSERT (total == role_info->legal_start_index);
            total += role_info->num_inputs_legals;
        }
    }

    ASSERT (total == this->num_components);

    // assign to current state
    Component* base = this->components;
    for (int ii=0; ii<this->num_bases; ii++, base++) {
        this->current_state->set(ii, base->count == 0);
    }

    // assign to transitions state
    Component* transition = this->components + this->transitions_index;
    for (int ii=0; ii<this->num_bases; ii++, transition++) {
        this->transition_state->set(ii, transition->count == 0);
    }

    // sync up legals one time - after we are on trigger alert!
    for (int ii=0; ii<this->role_count; ii++) {
        RoleInfo* role_info = this->roles + ii;
        ASSERT (role_info->legal_state.getCount() == 0);
        if (role_info->legal_start_index != -1) {
            Component* legal = this->components + role_info->legal_start_index;
            for (int jj=0; jj<role_info->num_inputs_legals; jj++, legal++) {
                if (legal->count == 0) {
                    role_info->legal_state.insert(jj);
                }
            }
        }
    }

    // Set up instruction for trigger types
    for (int ii=0; ii<this->num_components; ii++) {
        Component* component = this->components + ii;

        component->role_index = 0;
        if (ii >= this->transitions_index && ii < this->transitions_index + this->num_bases) {
            ASSERT (component->instruction == NOUGHT);
            component->instruction = TRIGGER_TRANSITION;

        } else {
            for (int jj=0; jj<this->role_count; jj++) {
                RoleInfo* role_info = this->roles + jj;
                if (role_info->legal_start_index != -1) {
                    if (ii >= role_info->legal_start_index && ii < role_info->legal_start_index + role_info->num_inputs_legals) {
                        ASSERT (component->instruction == NOUGHT);
                        component->role_index = jj;
                        component->instruction = TRIGGER_LEGAL;
                    }
                }
            }
        }
    }

    for (int ii=0; ii<this->role_count; ii++) {
        this->preserve_last_move->set(ii, -1);
    }

    this->initialised = true;

    K273::l_info("StateMachine::recordFinalise() complete.");
}

void StateMachine::setMetaInformation(int component_id, const string& component_type,
                                      const string& gdl, const string& move, int goal_value) {
    MetaComponentInfo* info = this->metas + component_id;
    info->component_id = component_id;
    info->type = component_type;
    info->gdl = gdl;
    info->move = move;
    info->goal_value = goal_value;
}

void StateMachine::setInitialState(const BaseState* bs) {
    this->initial_state->assign(bs);
}

BaseState* StateMachine::newBaseState() const {
    BaseState* bs = static_cast<BaseState*> (malloc(BaseState::mallocSize(this->num_bases)));
    bs->init(this->num_bases);
    return bs;
}

const GGPLib::BaseState* StateMachine::getCurrentState() const {
    return this->current_state;
}

void StateMachine::updateBases(const BaseState* bs) {
    const BaseState::ArrayType *pt_bs = bs->data;
    BaseState::ArrayType *pt_current = this->current_state->data;
    for (int block=0; block<bs->byte_count; block++) {
        BaseState::ArrayType xxor = *pt_bs ^ *pt_current;
        Component* base = this->components + block * BaseState::ARRAYTYPE_BITS;
        for (int ii=0; ii<BaseState::ARRAYTYPE_BITS; ii++) {
            const BaseState::ArrayType mask = (BaseState::ArrayType(1) << ii);
            if (xxor & mask) {
                this->propagate(base + ii, *pt_bs & mask);
            }
        }

        pt_bs++;
        pt_current++;
    }

    this->current_state->assign(bs);
}

LegalState* StateMachine::getLegalState(int role_index) {
    RoleInfo* role = this->roles + role_index;
    return &role->legal_state;
}

const char* StateMachine::getGDL(int index) const {
    MetaComponentInfo* info = this->metas + index;
    return info->gdl.c_str();
}

const char* StateMachine::legalToMove(int role_index, int choice) const {
    const RoleInfo* role_info = &this->roles[role_index];
    int legal_index = role_info->legal_start_index + choice;
    const MetaComponentInfo* info = this->metas + legal_index;
    return info->move.c_str();
}

JointMove* StateMachine::getJointMove() {
    // zero array size malloc
    JointMove* move = static_cast<JointMove*> (malloc(JointMove::mallocSize(this->role_count)));
    move->setSize(this->role_count);
    return move;
}

bool StateMachine::isTerminal() const {
    Component* terminal = this->components + this->terminal_index;
    if (terminal->count == 0) {
        return true;
    }

    return false;
}

void StateMachine::nextState(const JointMove* move, BaseState* bs) {
    // Constraint: state of network should be correct wrt bases
    // IMPORTANT - this does not update the bases at the end.

    // propagate inputs
    for (int ii=0; ii<this->role_count; ii++) {
        int last = this->preserve_last_move->get(ii);
        int cur = move->get(ii);
        if (last != cur) {
            // preserve for next time
            this->preserve_last_move->set(ii, cur);

            RoleInfo* role_info = &this->roles[ii];
            int input_start_index = role_info->input_start_index;

            Component* input = this->components + (input_start_index + cur);
            Component** pt_output = this->component_outputs + input->output_index;

            this->forwardPropagateValueP(pt_output);
            //this->propagate(input, true);
            if (last != -1) {
                input = this->components + (input_start_index + last);
                pt_output = this->component_outputs + input->output_index;
                this->forwardPropagateValueN(pt_output);
                //this->propagate(input, false);
            }
        }
    }

    // read from transitions into base state
    bs->assign(this->transition_state);

    // OLD CODE WITHOUT PRESERVE:
    //     // propagate inputs
    //     for (int ii=0; ii<this->role_count; ii++) {
    //         RoleInfo* role_info = &this->roles[ii];
    //         int input_index = role_info->input_start_index + move->get(ii);

    //         Component* input = this->components + input_index;
    //         Component** pt_output = this->component_outputs + input->output_index;

    //         this->forwardPropagateValueP(pt_output);
    //     }

    //     // read from transitions into base state
    //     bs->assign(this->transition_state);

    //     // propagate inputs
    //     for (int ii=0; ii<this->role_count; ii++) {
    //         RoleInfo* role_info = &this->roles[ii];
    //         int input_index = role_info->input_start_index + move->get(ii);

    //         Component* input = this->components + input_index;
    //         Component** pt_output = this->component_outputs + input->output_index;

    //         this->forwardPropagateValueN(pt_output);
    //     }
    // }
}

int StateMachine::getGoalValue(int role_index) {
    RoleInfo* role_info = &this->roles[role_index];
    Component* goal = this->components + role_info->goal_start_index;
    for (int ii=0; ii<role_info->num_goals; ii++, goal++) {
        if (goal->count == 0) {
            // get the meta
            MetaComponentInfo* info = this->metas + role_info->goal_start_index + ii;
            return info->goal_value;
        }
    }

    return -1;
}

void StateMachine::reset() {
    this->updateBases(this->initial_state);
    for (int ii=0; ii<this->role_count; ii++) {
        int last = this->preserve_last_move->get(ii);
        if (last != -1) {
            RoleInfo* role_info = &this->roles[ii];
            int input_start_index = role_info->input_start_index;

            Component* input = this->components + (input_start_index + last);
            Component** pt_output = this->component_outputs + input->output_index;
            this->forwardPropagateValueN(pt_output);
        }

        this->preserve_last_move->set(ii, -1);
    }
}

void StateMachine::triggerPropagateLegalP(Component* component) {
    int component_id = component - this->components;
    RoleInfo* role = &this->roles[component->role_index];

    role->legal_state.insert(component_id - role->legal_start_index);
}

void StateMachine::triggerPropagateTransitionP(Component* component) {
    int component_id = component - this->components;
    this->transition_state->set(component_id - this->transitions_index, true);
}

void StateMachine::triggerPropagateLegalN(Component* component) {
    int component_id = component - this->components;
    RoleInfo* role = &this->roles[component->role_index];

    role->legal_state.remove(component_id - role->legal_start_index);
}


void StateMachine::triggerPropagateTransitionN(Component* component) {
    int component_id = component - this->components;
    this->transition_state->set(component_id - this->transitions_index, false);
}

void StateMachine::forwardPropagateValueP(Component** pt_output) {
    // CONSTRAINT: only called if propagation is required
    while (*pt_output != nullptr) {
        this->forwardPropagateValueP1(pt_output++);
    }
}

void StateMachine::forwardPropagateValueN(Component** pt_output) {
    // CONSTRAINT: only called if propagation is required
    while (*pt_output != nullptr) {
        this->forwardPropagateValueN1(pt_output++);
    }
}
