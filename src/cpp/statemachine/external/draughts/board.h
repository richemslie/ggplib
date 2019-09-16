#pragma once

// local includes
#include "desc.h"

// ggplib includes
#include <statemachine/jointmove.h>
#include <statemachine/legalstate.h>
#include <statemachine/basestate.h>

// k273 includes
#include <k273/exception.h>
#include <k273/stacktrace.h>

// std includes
#include <vector>
#include <cstdint>


namespace InternationalDraughts {

    class Board {

    public:
        Board(const Description* board_desc,
              bool breakthrough_mode=false,
              bool killer_mode=false);

        ~Board();

    private:
        Square* get(Position pos) {
            return this->squares + (pos - 1);
        }

        // indexed from 1...
        const Square* get(Position pos) const {
            return this->squares + (pos - 1);
        }

        int getStepCount() const;
        void incrStepCount(bool reset);

        Square* getMeta() {
            return this->squares + this->board_desc->getMetaSquareIncr();
        }

        const Square* getMeta() const {
            return this->squares + this->board_desc->getMetaSquareIncr();
        }

        void setSquares(GGPLib::BaseState* bs) {
            this->squares = (Square*) bs->data;
        }

        void clearCaptures();

        void pushLegal(Role role, Legal legal);
        void pushLegalNoop(Role role);
        void clearLegals(Role role);

        void nonCaptureLegals(Role role, Position pos, Piece what);
        int maximalLegals(Role role, Position pos, Piece what, int best_mc=0);
        int maximalCaptures(Role role, Position pos, Piece what);
        void updateLegalsChoices();
        int capturedFrom(Role role, Position from_pos, Position to_pos,
                         Piece what, Direction direction);
        void playMove(const GGPLib::JointMove* move);

        bool done() const;
        int score(Role role) const;

    private:
        class ImmediateCaptures;
        friend class SM;
        friend class ImmediateCaptures;
        const Description* board_desc;

        const bool breakthrough_mode;
        const bool killer_mode;

        GGPLib::LegalState* white_legalstate;
        GGPLib::LegalState* black_legalstate;

        Square* squares;
    };
}
