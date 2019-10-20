#include "statemachine/external/hex/desc.h"
#include "statemachine/external/hex/sm.h"

#include <k273/util.h>
#include <k273/logging.h>
#include <k273/exception.h>

using namespace K273;
using namespace GGPLib;

static void logExceptionWrapper(const std::string& name) {
    try {
        K273::l_critical("an exception was thrown in in %s:", name.c_str());
        throw;

    } catch (const K273::Exception& exc) {
        K273::l_critical("K273::Exception Message : %s", exc.getMessage().c_str());
        K273::l_critical("K273::Exception Stacktrace : \n%s", exc.getStacktrace().c_str());

    } catch (std::exception& exc) {
        K273::l_critical("std::exception What : %s", exc.what());

    } catch (...) {
        K273::l_critical("Unknown exception");
    }
}

static void testDescription() {
    HexGame::Description* desc = new HexGame::Description(7, true);

    ASSERT(desc->getBoadSize() == 7);
    ASSERT(desc->canSwap());
    ASSERT(desc->numberPoints() == 49);

    ASSERT(desc->legalsSize(HexGame::Role::Black) == desc->numberPoints() + 1);
    ASSERT(desc->legalsSize(HexGame::Role::White) == desc->numberPoints() + 2);

    for (int ii=0; ii<desc->numberPoints(); ii++) {
        K273::l_debug("%s %s",
                      desc->legalToMove(HexGame::Role::Black, desc->blackPosToLegal(ii)),
                      desc->legalToMove(HexGame::Role::White, desc->whitePosToLegal(ii)));
    }

    for (int ii=0; ii<desc->numberPoints(); ii++) {
        HexGame::Cell cell = desc->getCell(HexGame::Role::Black, ii);
        K273::l_debug("%d %s", ii, cell.repr().c_str());
    }

    for (int ii=0; ii<desc->numberPoints(); ii++) {
        HexGame::Cell cell = desc->getCell(HexGame::Role::White, ii);
        K273::l_debug("%d %s", ii, cell.repr().c_str());
    }

    for (int ii : {0, 6, 7, 41, 48}) {
        for (int jj : desc->getNeighouringPositions(ii)) {
            K273::l_debug("%d n:%d", ii, jj);
        }
    }

    ASSERT(false);
}

int main() {
    K273::loggerSetup("test_hex.log", K273::Logger::LOG_VERBOSE);

    try {
        testDescription();
    } catch (...) {
        logExceptionWrapper(__PRETTY_FUNCTION__);
        throw;
    }

    HexGame::Description* desc = new HexGame::Description(7, true);
    GGPLib::StateMachineInterface* sm = new HexGame::SM(desc);
    sm->getInitialState();

    const int role_count = sm->getRoleCount();

    const int seconds_to_run = 10;

    const double start_time = get_time();
    const double end_time = start_time + seconds_to_run;

    int msecs_taken = 0;
    int rollouts = 0;
    int num_state_changes = 0;

    JointMove* joint_move = sm->getJointMove();
    BaseState* next_state = sm->newBaseState();
    K273::Random random;

    while (true) {
        sm->reset();
        ASSERT(!sm->isTerminal());
        K273::l_debug("HERE1");

        const double cur_time = get_time();
        if (cur_time > end_time) {
            msecs_taken = 1000 * (cur_time - start_time);
            break;
        }

        int depth = 0;

        while (true) {
            if (sm->isTerminal()) {
                break;
            }

            // populate joint move
            for (int ii=0; ii<role_count; ii++) {
                const LegalState* ls = sm->getLegalState(ii);
                int x = random.getWithMax(ls->getCount());
                int choice = ls->getLegal(x);
                joint_move->set(ii, choice);
            }

            K273::l_debug("%s %s",
                          desc->legalToMove(HexGame::Role::Black, joint_move->get(0)),
                          desc->legalToMove(HexGame::Role::White, joint_move->get(1)));

            sm->nextState(joint_move, next_state);
            sm->updateBases(next_state);

            depth++;
        }

        // for heating the cpu side effect only
        for (int ii=0; ii<sm->getRoleCount(); ii++) {
            sm->getGoalValue(ii);
        }

        rollouts++;
        num_state_changes += depth;
    }


}
