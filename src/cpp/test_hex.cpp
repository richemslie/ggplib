#include "statemachine/external/hex/desc.h"
#include "statemachine/external/hex/sm.h"

#include <k273/util.h>
#include <k273/logging.h>
#include <k273/exception.h>

using namespace K273;
using namespace GGPLib;
using namespace HexGame;

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
    return;
    Description* desc = new Description(7, true);

    ASSERT(desc->getBoadSize() == 7);
    ASSERT(desc->canSwap());
    ASSERT(desc->numberPoints() == 49);

    ASSERT(desc->legalsSize(Role::Black) == desc->numberPoints() + 1);
    ASSERT(desc->legalsSize(Role::White) == desc->numberPoints() + 2);

    K273::l_debug("legals!");
    for (int ii=0; ii<desc->numberPoints(); ii++) {
        K273::l_debug("%s %s",
                      desc->legalToMove(Role::Black, desc->blackPosToLegal(ii)),
                      desc->legalToMove(Role::White, desc->whitePosToLegal(ii)));
    }

    K273::l_debug("get cells black!");
    for (int ii=0; ii<desc->numberPoints(); ii++) {
        Cell cell = desc->getCell(Role::Black, ii);
        K273::l_debug("%d %s", ii, cell.repr().c_str());
    }

    K273::l_debug("get cells white!");
    for (int ii=0; ii<desc->numberPoints(); ii++) {
        Cell cell = desc->getCell(Role::White, ii);
        K273::l_debug("%d %s", ii, cell.repr().c_str());
    }

    K273::l_debug("get neighbours!");
    for (int ii : {0, 6, 7, 32, 41, 48}) {
        for (int jj : desc->getNeighouringPositions(ii)) {
            K273::l_debug("%d n:%d", ii, jj);
        }
    }
}

static void testBoard() {
    return;
    Description* desc = new Description(7, true);
    GGPLib::StateMachineInterface* sm = new SM(desc);

    Cell* cells = (Cell*) sm->getInitialState()->data;

    for (int ii=0; ii<desc->numberPoints(); ii++) {
        K273::l_debug("%d %s", ii, cells->repr().c_str());
        cells++;
    }

    MetaCell* meta = (MetaCell*) cells;
    K273::l_debug(meta->repr());
}


static void test_walkAcross() {
    Description* desc = new Description(5, true);
    GGPLib::StateMachineInterface* sm = new SM(desc);
    sm->reset();

    JointMove* joint_move = sm->getJointMove();
    BaseState* next_state = sm->newBaseState();

    // noop
    joint_move->set(1, 0);

    for (int ii=0; ii<5; ii++) {
        int pos = 3 + ii * 5;
        joint_move->set(0, pos + 1);

        K273::l_debug("%d %s %s", ii,
                      desc->legalToMove(Role::Black, joint_move->get(0)),
                      desc->legalToMove(Role::White, joint_move->get(1)));

        sm->nextState(joint_move, next_state);
        sm->updateBases(next_state);

        Cell* cells = (Cell*) sm->getCurrentState()->data;
        for (int ii=0; ii<desc->numberPoints(); ii++) {
            K273::l_debug("%d %s", ii, cells->repr().c_str());
            cells++;
        }

        MetaCell* meta = (MetaCell*) cells;
        meta->switchTurn();
    }

    ASSERT(sm->isTerminal());
    ASSERT(sm->getGoalValue(0) == 100);
    ASSERT(sm->getGoalValue(1) == 0);
}

static void test_walkAcross2() {
    Description* desc = new Description(5, true);
    GGPLib::StateMachineInterface* sm = new SM(desc);
    sm->reset();

    JointMove* joint_move = sm->getJointMove();
    BaseState* next_state = sm->newBaseState();

    // noop
    joint_move->set(1, 0);

    for (int ii=4; ii>=0; ii--) {
        int pos = 3 + ii * 5;
        joint_move->set(0, pos + 1);

        K273::l_debug("%d %s %s", ii,
                      desc->legalToMove(Role::Black, joint_move->get(0)),
                      desc->legalToMove(Role::White, joint_move->get(1)));

        sm->nextState(joint_move, next_state);
        sm->updateBases(next_state);

        Cell* cells = (Cell*) sm->getCurrentState()->data;
        for (int ii=0; ii<desc->numberPoints(); ii++) {
            K273::l_debug("%d %s", ii, cells->repr().c_str());
            cells++;
        }

        MetaCell* meta = (MetaCell*) cells;
        meta->switchTurn();
    }

    ASSERT(sm->isTerminal());
    ASSERT(sm->getGoalValue(0) == 100);
    ASSERT(sm->getGoalValue(1) == 0);
}


static void test_walkAcross3() {
    Description* desc = new Description(5, true);
    GGPLib::StateMachineInterface* sm = new SM(desc);
    sm->reset();

    JointMove* joint_move = sm->getJointMove();
    BaseState* next_state = sm->newBaseState();

    // noop
    joint_move->set(1, 0);

    for (int ii=4; ii>=3; ii--) {
        int pos = 3 + ii * 5;
        joint_move->set(0, pos + 1);

        K273::l_debug("%d %s %s", ii,
                      desc->legalToMove(Role::Black, joint_move->get(0)),
                      desc->legalToMove(Role::White, joint_move->get(1)));

        sm->nextState(joint_move, next_state);
        sm->updateBases(next_state);

        Cell* cells = (Cell*) sm->getCurrentState()->data;
        for (int ii=0; ii<desc->numberPoints(); ii++) {
            K273::l_debug("%d %s", ii, cells->repr().c_str());
            cells++;
        }

        MetaCell* meta = (MetaCell*) cells;
        meta->switchTurn();
    }

    for (int ii=0; ii<2; ii++) {
        int pos = 3 + ii * 5;
        joint_move->set(0, pos + 1);

        K273::l_debug("%d %s %s", ii,
                      desc->legalToMove(Role::Black, joint_move->get(0)),
                      desc->legalToMove(Role::White, joint_move->get(1)));

        sm->nextState(joint_move, next_state);
        sm->updateBases(next_state);

        Cell* cells = (Cell*) sm->getCurrentState()->data;
        for (int ii=0; ii<desc->numberPoints(); ii++) {
            K273::l_debug("%d %s", ii, cells->repr().c_str());
            cells++;
        }

        MetaCell* meta = (MetaCell*) cells;
        meta->switchTurn();
    }

    {
        int ii = 2;
        int pos = 3 + ii * 5;
        joint_move->set(0, pos + 1);

        K273::l_debug("%d %s %s", ii,
                      desc->legalToMove(Role::Black, joint_move->get(0)),
                      desc->legalToMove(Role::White, joint_move->get(1)));

        sm->nextState(joint_move, next_state);
        sm->updateBases(next_state);

        Cell* cells = (Cell*) sm->getCurrentState()->data;
        for (int ii=0; ii<desc->numberPoints(); ii++) {
            K273::l_debug("%d %s", ii, cells->repr().c_str());
            cells++;
        }

        MetaCell* meta = (MetaCell*) cells;
        meta->switchTurn();
    }

    ASSERT(sm->isTerminal());
    ASSERT(sm->getGoalValue(0) == 100);
    ASSERT(sm->getGoalValue(1) == 0);
}

int main() {
    K273::loggerSetup("test_hex.log", K273::Logger::LOG_VERBOSE);

    try {
        test_walkAcross3();
    } catch (...) {
        logExceptionWrapper(__PRETTY_FUNCTION__);
        throw;
    }

    try {
        testDescription();
    } catch (...) {
        logExceptionWrapper(__PRETTY_FUNCTION__);
        throw;
    }

    try {
        testBoard();
    } catch (...) {
        logExceptionWrapper(__PRETTY_FUNCTION__);
        throw;
    }

    try {
        test_walkAcross();
        test_walkAcross2();
    } catch (...) {
        logExceptionWrapper(__PRETTY_FUNCTION__);
        throw;
    }

    Description* desc = new Description(19, true);
    GGPLib::StateMachineInterface* sm = new SM(desc);
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

    K273::l_debug("rollouts %d, changes %d", rollouts / seconds_to_run, num_state_changes);
}
