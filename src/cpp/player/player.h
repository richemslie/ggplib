#pragma once

#include "statemachine/statemachine.h"
#include "statemachine/jointmove.h"

#include <k273/util.h>
#include <k273/logging.h>
#include <k273/strutils.h>

#include <string>

namespace GGPLib {

    class PlayerBase {
        /* abstract interface. */

    public:
        PlayerBase(StateMachineInterface* sm, int player_role_index) :
            sm(sm),
            our_role_index(player_role_index),
            game_depth(0) {
        }

        virtual ~PlayerBase() {
            delete this->sm;
        }

    public:
        // implement these:
        virtual void onMetaGaming(double end_time) {
        }

        // called before apply move.  Gives the player an oppurtunity to return
        // any debug/extra information.
        virtual std::string beforeApplyInfo() {
            return "";
        }

        virtual void onApplyMove(JointMove* move) {
        }


        virtual int onNextMove(double end_time) = 0;

    protected:
        StateMachineInterface* sm;
        int our_role_index;
        int game_depth;
    };

}
