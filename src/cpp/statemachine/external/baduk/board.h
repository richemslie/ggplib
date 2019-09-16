#pragma once

// local includes
#include "desc.h"

// ggplib includes
#include <statemachine/jointmove.h>
#include <statemachine/legalstate.h>
#include <statemachine/basestate.h>

// std includes
#include <string>
#include <vector>

namespace Baduk {

    enum Colour {
        EMPTY = 0,
        BLACK = 1,
        WHITE = 2
    };

    inline Colour opposite(Colour colour) {
        if (colour == BLACK) {
            return WHITE;

        } else if (colour == WHITE) {
            return BLACK;
        }

        return colour;
    }

    class Chain;

    struct Point {
        int x;
        int y;
        int index;

        Colour colour;
        Chain* chain;

        Point* neighbouring_points[4];
    };

    // a 32 bit integer
    using PointIndex = int;

    // typedef this?
    class Chain {
    public:
        Chain() {
        }

        // called once via object pool
        void init(const int max_board_size);

        // called each time on acquiring from pool
        void acquire(Colour colour);

    public:
        bool inAtari() const {
            return this->liberty_count == 1;
        }

        void addLiberty(PointIndex pi) {
            this->liberties[pi] = true;
            this->liberty_count += 1;
        }

        bool hasLiberty(PointIndex pi) const {
            return this->liberties[pi];
        }

        void removeLiberty(PointIndex pi) {
            this->liberties[pi] = false;
            this->liberty_count -= 1;
        }

        void addPoint(PointIndex pi) {
            this->points.push_back(pi);
            this->point_count++;
        }

        const std::vector <PointIndex>& getPoints() const {
            return this->points;
        }

    public:
        int getLibertyCount() const {
            return this->liberty_count;
        }

        int getPointCount() const {
            return this->point_count;
        }


    public:
        Colour colour;

    private:
        int max_board_size;

        std::vector <PointIndex> points;
        int point_count;

        // this is fastest just as an array, and using memset.  tried other tricks
        int liberty_count;

        // could malloc it this way
        bool* liberties;

        friend class Board;
    };


    // This is a fast update result, we avoid exceptions for control flow.  Note we actually return the
    // captured for the update.  This is so we don't need a listener on the board for when chains are
    // captured.

    struct TestResult {
        enum ResultFailReason {
            None,
            Suicide,
            Ko,
            OnTopOfStone
        };

        Chain* captured[4];
        Chain* connexions[4];
        int captured_count;
        int connexions_count;

        PointIndex new_ko_point;
        PointIndex new_ko_captured_point;

        ResultFailReason reason;

        void reset() {
            for (int ii=0; ii<4; ii++) {
                this->captured[ii] = nullptr;
                this->connexions[ii] = nullptr;
            }

            this->captured_count = 0;
            this->connexions_count = 0;

            this->new_ko_point = -1;
            this->new_ko_captured_point = -1;
            this->reason = TestResult::None;
        }
    };

    class Board {
        /* this is stateful... */

    public:
        Board(const Description* board_desc, bool disallow_early_double_pass=true);
        ~Board();

    private:
        // intialisation only
        void getNeighbouringPoints(Point* point, Point** neighbouring_points);

    public:
        int toPointIndex(int x, int y) const {
            return y * this->board_desc->getBoadSize() + x;
        }

        Point* getPointByIndex(int index) {
            return &this->state[index];
        }

        void reset();
        void setFromBS(const GGPLib::BaseState* bs);
        void setToBS(GGPLib::BaseState* bs);

        bool testPoint(const Point* point, Colour player);
        void updatePoint(Point* point, Colour player);

        void playMove(const GGPLib::JointMove* move);
        bool finished() const;
        float actualScore() const;

        bool oneEye(Point* point, Colour player);
        void moveGen(GGPLib::LegalState* white, GGPLib::LegalState* black);

    public:
        // testing XXX
        const TestResult& getTestResult() {
            return this->result;
        }

    private:
        K273::ObjectPool <Chain>* chain_pool;
        const Description* board_desc;
        const bool disallow_early_double_pass;

        int turn_role_index;
        PointIndex ko_point;
        PointIndex ko_captured_point;
        bool white_passed;
        bool black_passed;

        std::vector <Point> state;
        TestResult result;
    };

}
