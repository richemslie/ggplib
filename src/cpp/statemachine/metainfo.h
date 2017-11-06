#pragma once

#include <k273/strutils.h>

namespace GGPLib {
    struct MetaComponentInfo {
        MetaComponentInfo() :
            component_id(-1),
            goal_value(-1) {
        }

        // component_id
        int component_id;

        std::string type;

        // May not be set
        std::string gdl;
        std::string move;

        // integer 0-100 value (-1 not set)
        int goal_value;

        std::string repr() const {
            if (this->gdl.size()) {
                return K273::fmtString("%s(%d - %s)", this->type.c_str(), this->component_id, this->gdl.c_str());
            } else {
                return K273::fmtString("%s(%d)", this->type.c_str(), this->component_id);
            }
        }
    };
}
