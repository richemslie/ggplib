#include "legalplayer.h"

using namespace K273;
using namespace GGPLib;
using namespace LegalPlayer;

int Player::onNextMove(double end_time) {
    LegalState* ls = this->sm->getLegalState(this->our_role_index);
    return ls->getLegal(0);
}
