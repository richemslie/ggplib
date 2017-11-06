#include "statemachine/combined.h"

#include "statemachine/legalstate.h"
#include "statemachine/jointmove.h"
#include "statemachine/metainfo.h"
#include "statemachine/roleinfo.h"

#include <vector>

using namespace GGPLib;

///////////////////////////////////////////////////////////////////////////////

CombinedStateMachine::CombinedStateMachine(int number_control_states) :
    number_control_states(number_control_states),
    goal_sm(nullptr),
    current(nullptr) {
    this->controls = new ControlInfo[number_control_states];
}

CombinedStateMachine::~CombinedStateMachine() {
    if (this->goal_sm != nullptr) {
        delete this->goal_sm;
    }

    ControlInfo* control = this->controls;
    for (int ii=0; ii<this->number_control_states; ii++, control++) {
        delete control->sm;
    }

    delete[] this->controls;
}

void CombinedStateMachine::setGoalStateMachine(StateMachine* goal_sm) {
    this->goal_sm = goal_sm;
}

void CombinedStateMachine::setControlStateMachine(int control_index, int control_cid, StateMachine* control_sm) {
    ControlInfo* info = this->controls + control_index;
    info->control_index = control_index;
    info->control_cid = control_cid;
    info->sm = control_sm;
}

///////////////////////////////////////////////////////////////////////////////

StateMachineInterface* CombinedStateMachine::dupe() const {
    CombinedStateMachine* d = new CombinedStateMachine(this->number_control_states);
    if (this->goal_sm != nullptr) {
        d->goal_sm = static_cast<StateMachine*> (this->goal_sm->dupe());
    }

    for (int ii=0; ii<this->number_control_states; ii++) {
        ControlInfo* d_info = d->controls + ii;
        const ControlInfo* this_info = this->controls + ii;

        d_info->control_index = this_info->control_index;
        d_info->control_cid = this_info->control_cid;
        d_info->sm = static_cast<StateMachine*> (this_info->sm->dupe());

        if (this->current == this_info->sm) {
            d->current = d_info->sm;
        }
    }

    return d;
}

///////////////////////////////////////////////////////////////////////////////

ControlInfo* CombinedStateMachine::getControl(const BaseState* bs) {
    ControlInfo* new_control = nullptr;

    ControlInfo* control = this->controls;
    for (int ii=0; ii<this->number_control_states; ii++, control++) {
        if (bs->get(control->control_cid)) {
            //ASSERT (new_control == nullptr);
            new_control = control;
        }
    }

    //ASSERT (new_control != nullptr);
    return new_control;
}

void CombinedStateMachine::reset() {
    ControlInfo* control = this->controls;
    for (int ii=0; ii<this->number_control_states; ii++, control++) {
        control->sm->reset();
    }

    control = this->controls;
    this->current = this->getControl(control->sm->getCurrentState())->sm;
}

