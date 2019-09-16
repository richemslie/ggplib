#pragma once

// std includes
#include <string>
#include <vector>
#include <cstdint>
#include <type_traits>

// k273 includes
#include <k273/util.h>

// ggplib includes
#include <statemachine/basestate.h>
#include <statemachine/jointmove.h>

///////////////////////////////////////////////////////////////////////////////

namespace Baduk {

    enum class Role : int {Black = 0, White=1};
    using Legal = int;

    class Description {
    public:
        Description(int board_size);
        ~Description();

    private:
        // generated code
        void initBoard_9x9();
        void initBoard_13x13();
        void initBoard_19x19();

    public:
        int getBoadSize() const {
            return this->board_size;
        }

        int numberPoints() const {
            return this->board_size * this->board_size;
        }

        float getKomi() const {
            return this->komi;
        }

        Legal getNoopLegal() const {
            return 0;
        }

        Legal getPassLegal() const {
            return 1;
        }

        int getLegal(int board_index) const {
            return board_index + 2;
        }

        void setInitialState(GGPLib::BaseState* bs) const;
        const char* legalToMove(int role_index, Legal legal) const;
        int legalsSize(Role role) const;

    private:
        const int board_size;

        float komi;

        std::vector <const char*> white_legal_moves;
        std::vector <const char*> black_legal_moves;

        std::vector <bool> initial_state;
    };
}
