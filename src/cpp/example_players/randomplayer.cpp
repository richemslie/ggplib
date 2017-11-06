#include "randomplayer.h"

using namespace K273;
using namespace GGPLib;
using namespace RandomPlayer;

int Player::onNextMove(double end_time) {
    LegalState* ls = this->sm->getLegalState(this->our_role_index);
    return ls->getLegal(this->random.getWithMax(ls->getCount()));
}
