#include "board.h"

// k273 includes
#include <k273/logging.h>
#include <k273/strutils.h>
#include <k273/exception.h>
#include <k273/util.h>

#include <cstring>

using namespace Baduk;

void Chain::init(const int sz) {
    this->max_board_size = sz;
    this->points.reserve(this->max_board_size);
    this->liberties = (bool*) malloc(sizeof(bool[this->max_board_size]));
}

void Chain::acquire(Colour colour) {
    this->points.clear();
    this->colour = colour;
    this->point_count = 0;
    this->liberty_count = 0;
    // memset raw memory more than twice as fast as stl:fill...
    ::memset(this->liberties, 0, sizeof(bool[this->max_board_size]));
}

// ZZZ to board_desc
void Board::getNeighbouringPoints(Point* point, Point** neighbours) {
    int index = 0;

    // x goes left to right
    // y goes from bottom to top

    // left
    if (point->x > 0) {
        neighbours[index++] = &this->state[this->toPointIndex(point->x - 1, point->y)];
    }

    // lower
    if (point->y > 0) {
        neighbours[index++] = &this->state[this->toPointIndex(point->x, point->y - 1)];
    }

    // right
    if (point->x < this->board_desc->getBoadSize() - 1) {
        neighbours[index++] = &this->state[this->toPointIndex(point->x + 1, point->y)];
    }

    // upper
    if (point->y < this->board_desc->getBoadSize() - 1) {
        neighbours[index++] = &this->state[this->toPointIndex(point->x, point->y + 1)];
    }

    for (; index<4; index++) {
        neighbours[index] = nullptr;
    }
}

Board::Board(const Description* board_desc, bool disallow_early_double_pass) :
    board_desc(board_desc),
    disallow_early_double_pass(disallow_early_double_pass),
    ko_point(-1) {

    K273::l_debug("board size %d", this->board_desc->getBoadSize());

    auto chain_init = [board_desc] (Chain* c) {
        c->init(board_desc->getBoadSize() * board_desc->getBoadSize());
    };

    chain_pool = new K273::ObjectPool <Chain>(10000, chain_init);

    this->state.resize(board_desc->getBoadSize() * board_desc->getBoadSize());

    int ii=0;
    for (int yy=0; yy<this->board_desc->getBoadSize(); yy++) {
        for (int xx=0; xx<this->board_desc->getBoadSize(); xx++) {
            Point& point = this->state[ii];
            point.x = xx;
            point.y = yy;
            point.index = yy * this->board_desc->getBoadSize() + xx;

            point.chain = nullptr;
            point.colour = EMPTY;

            this->getNeighbouringPoints(&point, point.neighbouring_points);

            ii++;
        }
    }
}

Board::~Board() {
    this->reset();
}

void Board::reset() {
    for (int ii=0; ii<this->board_desc->numberPoints(); ii++) {
        Point& point = this->state[ii];

        // return chain to pool
        if (point.chain != nullptr) {
            Chain* chain = point.chain;
            for (const PointIndex pi : chain->points) {
                this->state[pi].chain = nullptr;
            }

            this->chain_pool->release(chain);
            point.chain = nullptr;
        }

        point.colour = EMPTY;
    }

    this->ko_point = -1;
    this->ko_captured_point = -1;

    this->turn_role_index = 0;
}

Colour getColourFromBS(int pos, const GGPLib::BaseState* bs) {
    int indx = pos * 4;
    if (bs->get(indx)) {
        return BLACK;
    } else if (bs->get(indx + 1)) {
        return WHITE;
    }

    return EMPTY;
}

void setColourToBS(int pos, Colour colour, GGPLib::BaseState* bs) {
    // ZZZ XXX this could be much optimised using bitwize constants

    // K273::l_debug("setColourToBS %d, %d", pos, colour);
    int indx = pos * 4;
    if (colour == BLACK) {
        bs->set(indx, 1);
        bs->set(indx + 1, 0);

    } else if (colour == WHITE) {
        bs->set(indx, 0);
        bs->set(indx + 1, 1);

    } else {
        bs->set(indx, 0);
        bs->set(indx + 1, 0);
    }

    bs->set(indx + 2, 0);
    bs->set(indx + 3, 0);
}

void Board::setFromBS(const GGPLib::BaseState* bs) {
    this->reset();

    // super slow version
    for (int ii=0; ii<this->board_desc->numberPoints(); ii++) {
        Point& point = this->state[ii];

        Colour colour = getColourFromBS(ii, bs);
        if (colour != EMPTY) {
            ASSERT(this->testPoint(&point, colour));
            this->updatePoint(&point, colour);
        }
    }

    const int control_black = this->board_desc->numberPoints() * 4;
    const int control_white = this->board_desc->numberPoints() * 4 + 1;
    this->black_passed = bs->get(this->board_desc->numberPoints() * 4 + 2);
    this->white_passed = bs->get(this->board_desc->numberPoints() * 4 + 3);
    const int is_ko_set = this->board_desc->numberPoints() * 4 + 4;

    ASSERT(!(bs->get(control_black) && bs->get(control_white)));
    ASSERT(bs->get(control_black) || bs->get(control_white));

    this->turn_role_index = bs->get(control_black) ? 0 : 1;

    // see addChain() in python version
    if (bs->get(is_ko_set)) {
        // K273::l_warning("Setting KO from BS");

        int not_done = 2;
        for (int ii=0; ii<this->board_desc->numberPoints(); ii++) {
            if (bs->get(ii * 4 + 2)) {
                ASSERT(this->ko_point == -1);
                this->ko_point = ii;
                not_done--;
            }

            if (bs->get(ii * 4 + 3)) {
                ASSERT(this->ko_captured_point == -1);
                this->ko_captured_point = ii;
                not_done--;
            }

            if (!not_done) {
                break;
            }
        }

        ASSERT(this->ko_point != -1 && this->ko_captured_point != -1);
    }
}

void Board::setToBS(GGPLib::BaseState* bs) {
    const int control_black = this->board_desc->numberPoints() * 4;
    const int control_white = this->board_desc->numberPoints() * 4 + 1;
    const int is_ko_set = this->board_desc->numberPoints() * 4 + 4;

    for (int ii=0; ii<this->board_desc->numberPoints(); ii++) {
        Point& point = this->state[ii];

        // Important : will unset ko bits
        setColourToBS(ii, point.colour, bs);
    }

    if (turn_role_index == 0) {
        bs->set(control_black, 1);
        bs->set(control_white, 0);

    } else {
        bs->set(control_black, 0);
        bs->set(control_white, 1);
    }

    bs->set(this->board_desc->numberPoints() * 4 + 2, this->black_passed);
    bs->set(this->board_desc->numberPoints() * 4 + 3, this->white_passed);

    if (this->ko_point != -1) {
        // K273::l_debug("Ko set! size %d %d", ko_point, ko_captured_point);

        bs->set(this->ko_point * 4 + 2, 1);
        bs->set(this->ko_captured_point * 4 + 3, 1);
        bs->set(is_ko_set, 1);
    } else {
        bs->set(is_ko_set, 0);
    }
}

bool Board::testPoint(const Point* point, Colour player) {
    TestResult* result = &this->result;
    result->reset();

    // cant play on top of a stone
    if (point->colour != EMPTY) {
        result->reason = TestResult::OnTopOfStone;
        return false;
    }

    // 1. we first want to gather the following info

    // keep a tally of many points we capture, regardless of number of chains
    int total_points_captured = 0;

    // guilty, until proven innocent!
    bool possible_suicide = true;

    // gather captured/connections
    for (Point* neighbour : point->neighbouring_points) {
        if (neighbour == nullptr) {
            break;
        }

        if (neighbour->colour == EMPTY) {
            possible_suicide = false;
            continue;
        }

        Chain* chain = neighbour->chain;

        // chains that are to be connected up
        if (chain->colour == player) {

            // if we connnect to a chain that has liberties, we are in the clear
            if (possible_suicide && !chain->inAtari()) {
                possible_suicide = false;
            }

            bool dupe = false;
            for (int ii=0; ii<result->connexions_count; ii++) {
                if (result->connexions[ii] == chain) {
                    dupe = true;
                    break;
                }
            }

            if (!dupe) {
                result->connexions[result->connexions_count++] = chain;
            }

            continue;

        } else {
            // chain->colour == opponent

            if (chain->inAtari()) {

                bool dupe = false;
                for (int ii=0; ii<result->captured_count; ii++) {
                    if (result->captured[ii] == chain) {
                        dupe = true;
                        break;
                    }
                }

                if (!dupe) {
                    result->captured[result->captured_count++] = chain;
                    total_points_captured += chain->point_count;
                    possible_suicide = false;
                }
            }
        }
    }

    if (possible_suicide) {
        result->reason = TestResult::Suicide;
        return false;
    }

    // check ko
    result->new_ko_point = -1;
    result->new_ko_captured_point = -1;

    // The idea here is that we can only return to previous state if we take the last stone
    if (total_points_captured == 1) {
        PointIndex captured_point = result->captured[0]->points[0];

        if (this->ko_point != -1) {
            // possible ko violation
            if (this->ko_point == captured_point && this->ko_captured_point == point->index) {
                result->reason = TestResult::Ko;
                return false;
            }
        }

        result->new_ko_point = point->index;
        result->new_ko_captured_point = captured_point;
    }

    return true;
}

void Board::updatePoint(Point* point, Colour player) {
    Colour opponent = opposite(player);

    // this will be set before entering here
    TestResult* result = &this->result;
    ASSERT(result->reason == TestResult::None);

    // 2. update state

    // connect any chains / create a new chain?
    Chain* thechain = nullptr;
    if (result->connexions_count) {

        // keep the longest chain
        for (Chain* chain : result->connexions) {
            if (chain == nullptr) {
                break;
            }

            if (thechain == nullptr) {
                thechain = chain;

            } else {
                if (chain->point_count > thechain->point_count) {
                    thechain = chain;
                }
            }
        }

        ASSERT(thechain != nullptr);

        // merge info from chains into one
        for (Chain* chain : result->connexions) {
            if (chain == nullptr) {
                break;
            }

            if (chain == thechain) {
                continue;
            }

            // XXX this seems highly inefficient... (should be possible to speed it up - also could use AVX ?)
            for (int libindex=0; libindex<board_desc->numberPoints(); libindex++) {
                if (chain->hasLiberty(libindex) && !thechain->hasLiberty(libindex)) {
                    thechain->addLiberty(libindex);
                }
            }

            for (PointIndex pi : chain->points) {
                thechain->addPoint(pi);
                Point* point = this->getPointByIndex(pi);
                point->chain = thechain;
            }

            // release the chain.
            this->chain_pool->release(chain);
        }

        // need to remove the new point as a liberty. (if we had to create a new chain, then we don't.  Hence the check.)
        if (thechain->hasLiberty(point->index)) {
            thechain->removeLiberty(point->index);
        }

    } else {
        // just create a new chain
        thechain = this->chain_pool->acquire(player);
    }

    // and add the merge point
    point->colour = player;
    point->chain = thechain;
    thechain->addPoint(point->index);

    // add / remove liberties
    for (Point* pp : point->neighbouring_points) {
        if (pp == nullptr) {
            break;
        }

        // this is adding the liberities to the *thechain*.
        if (pp->colour == EMPTY && !thechain->hasLiberty(pp->index)) {
            thechain->addLiberty(pp->index);
        }

        // this is removing the liberities for any opponent chains
        if (pp->colour == opponent) {
            // the neighbouring_points may be the same chain, so we check to see we haven't already removed it

            bool is_captured = false;
            for (int ii=0; ii<result->captured_count; ii++) {
                if (result->captured[ii] == pp->chain) {
                    is_captured = true;
                    break;
                }
            }

            if (!is_captured && pp->chain->hasLiberty(point->index)) {
                pp->chain->removeLiberty(point->index);
            }
        }
    }

    // remove any captured chains (captured_count is the number of chains)
    for (int ii=0; ii<result->captured_count; ii++) {
        Chain* chain = result->captured[ii];

        ASSERT(chain->liberty_count == 1);

        // actually remove, and add in any libearties
        for (PointIndex pi : chain->points) {
            Point* p = this->getPointByIndex(pi);
            p->colour = EMPTY;
            p->chain = nullptr;

            for (Point* neighbour : p->neighbouring_points) {
                if (neighbour == nullptr) {
                    break;
                }

                if (neighbour->colour == player) {
                    if (!neighbour->chain->hasLiberty(p->index)) {
                        neighbour->chain->addLiberty(p->index);
                    }
                }
            }
        }

        this->chain_pool->release(chain);
    }

    // update ko
    this->ko_point = result->new_ko_point;
    this->ko_captured_point = result->new_ko_captured_point;
}

void Board::playMove(const GGPLib::JointMove* move) {
    int opp_role_index = 1 - this->turn_role_index;
    ASSERT(move->get(opp_role_index) == this->board_desc->getNoopLegal());

    int legal = move->get(this->turn_role_index);
    bool passed = legal == this->board_desc->getPassLegal();
    if (!passed) {
        int point_index = legal - 2;
        Point* point = this->getPointByIndex(point_index);
        Colour colour = this->turn_role_index == 0 ? BLACK : WHITE;
        ASSERT(this->testPoint(point, colour));
        this->updatePoint(point, colour);

        this->white_passed = false;
        this->black_passed = false;

    } else {
        // ensure ko point is unset
        this->ko_point = -1;
        this->ko_captured_point = -1;

        // note whether passed
        if (this->turn_role_index) {
            this->white_passed = true;
        } else {
            this->black_passed = true;
        }
    }

    // swap turn
    this->turn_role_index = 1 - this->turn_role_index;
}

bool Board::finished() const {
    return this->black_passed && this->white_passed;
}

float Board::actualScore() const {
    // expects the board to be full... if in an ambigous state, will return -100000
    // returns number of points as white

    int points_score_black = 0;
    int points_score_white = 0;
    for (int ii=0; ii<this->board_desc->numberPoints(); ii++) {
        const Point& point = this->state[ii];

        if (point.colour == BLACK) {
            points_score_black++;

        } else if (point.colour == WHITE) {
            points_score_white++;

        } else {
            bool black_seen = false;
            bool white_seen = false;
            for (Point* neighbour : point.neighbouring_points) {
                if (neighbour != nullptr) {
                    if (neighbour->colour == BLACK) {
                        black_seen = true;
                    } else if (neighbour->colour == WHITE) {
                        white_seen = true;
                    } else {
                        return -100000;
                    }
                }
            }

            if (black_seen && white_seen) {
                continue;

            } else {
                if (white_seen) {
                    points_score_white++;

                } else if (black_seen) {
                    points_score_black++;

                } else {
                    ASSERT_MSG(false, "Can't happen");
                }
            }
        }
    }

    float white_score = this->board_desc->getKomi() + points_score_white - points_score_black;
    return white_score;
}

void Board::moveGen(GGPLib::LegalState* ls_black, GGPLib::LegalState* ls_white) {
    // clear the legal states
    ls_black->clear();
    ls_white->clear();

    // add noop for opponent
    GGPLib::LegalState* ls = nullptr;
    bool opponent_passed;
    if (this->turn_role_index == 0) {
        ls_white->insert(this->board_desc->getNoopLegal());
        ls = ls_black;
        opponent_passed = this->white_passed;
    } else {
        ls_black->insert(this->board_desc->getNoopLegal());
        ls = ls_white;
        opponent_passed = this->black_passed;
    }

    // add any points that are valid/legal, [**** and not filling one eyespace ****]
    Colour colour = this->turn_role_index == 0 ? BLACK : WHITE;
    for (int ii=0; ii<this->board_desc->numberPoints(); ii++) {
        Point& point = this->state[ii];

        if (this->testPoint(&point, colour)) {
            ls->insert(this->board_desc->getLegal(point.index));
        }
    }

    if (!opponent_passed) {
        ls->insert(this->board_desc->getPassLegal());

    } else {
        if (this->actualScore() > -1000) {
            ls->insert(this->board_desc->getPassLegal());
        } else {
            // failsafe. should never happen
            if (ls->getCount() == 0) {
                K273::l_warning("failsafe add pass since no legals left");
                ls->insert(this->board_desc->getPassLegal());
            }
        }
    }
}
