#pragma once

// local includes
#include "desc.h"

// ggplib includes
#include <statemachine/legalstate.h>
#include <statemachine/jointmove.h>

// stl includes
#include <stack>

namespace HexGame {

    // State of an in-play game.
    class Board {
    public:
        Board(const Description* board_desc) :
            board_desc(board_desc),
            cell_states(nullptr) {
        }

        ~Board() {
        }

    private:
        MetaCell* getMeta() {
            return (MetaCell*)(this->cell_states + this->board_desc->numberPoints());
        }

        const MetaCell* getMeta() const {
            MetaCell* meta = (MetaCell*)(this->cell_states + this->board_desc->numberPoints());
            return meta;
        }

        void swapFirstCell();

    public:
        void setCells(GGPLib::BaseState* bs) {
            this->cell_states = (Cell*) bs->data;
        }

        void playMove(const GGPLib::JointMove* move);

        void moveGen(GGPLib::LegalState* ls_black, GGPLib::LegalState* ls_white);

        bool finished() const;
        int score(Role role) const;

    private:
        const Description* board_desc;

        Cell* cell_states;
        std::stack <int> cells_to_check;
    };

}
