#pragma once

#include "player/player.h"
#include "statemachine/jointmove.h"
#include "statemachine/statemachine.h"

#include <k273/util.h>

namespace RandomPlayer {

    class Player : public GGPLib::PlayerBase {
        /* Plays - randomly. */

    public:
        Player(GGPLib::StateMachineInterface* sm, int our_role_index) :
            PlayerBase(sm, our_role_index) {
        }

        virtual ~Player() {
        }

    public:
        virtual int onNextMove(double end_time);

    private:
        K273::Random random;
    };
}
