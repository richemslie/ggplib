#pragma once

// std includes
#include <string>

// XXX why do we do this at all MAX_NUMBER_PLAYERS?
const int MAX_NUMBER_PLAYERS = 8;
#include "legalstate.h"

namespace GGPLib {

    struct RoleInfo {
        std::string name;
        int input_start_index;
        int legal_start_index;
        int goal_start_index;
        int num_inputs_legals;
        int num_goals;
        LegalState legal_state;
    };

}
