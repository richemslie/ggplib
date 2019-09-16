
// local includes
#include "desc.h"

// k273 includes
#include <k273/logging.h>
#include <k273/strutils.h>
#include <k273/exception.h>


using namespace Baduk;

///////////////////////////////////////////////////////////////////////////////

Description::Description(int sz) :
    board_size(sz) {

    K273::l_warning("Board size %d/%d", sz, this->board_size);

    // calls to generated code:

    if (this->board_size == 9) {
        this->initBoard_9x9();

    } else if (this->board_size == 13) {
        this->initBoard_13x13();

    } else if (this->board_size == 19) {
        this->initBoard_19x19();

    } else {
        ASSERT_MSG(false, "board size not supported");
    }
}

Description::~Description() {
    K273::l_warning("In Description::~Description()");
}

///////////////////////////////////////////////////////////////////////////////

void Description::setInitialState(GGPLib::BaseState* bs) const {
    // old style loop, so like enumerate
    for (std::size_t ii=0; ii<this->initial_state.size(); ++ii) {
        ASSERT((int) ii < bs->size);

        bs->set(ii, this->initial_state[ii]);
    }
}

const char* Description::legalToMove(int role_index, Legal legal) const {
    ASSERT(legal >= 0);
    if (role_index == 0) {
        ASSERT(legal < (int) this->white_legal_moves.size());
        return this->white_legal_moves[legal];
    } else {
        ASSERT(legal < (int) this->black_legal_moves.size());
        return this->black_legal_moves[legal];
    }
}

int Description::legalsSize(Role role) const {
    if (role == Role::White) {
        return this->white_legal_moves.size();
    } else {
        return this->black_legal_moves.size();
    }
}
