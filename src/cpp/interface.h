#pragma once

#define StateMachine void
#define BaseState void
#define LegalState void
#define JointMove void
#define CombinedSM void
#define PlayerBase void
#define DepthChargeTest void

#define boolean int

#ifdef __cplusplus
extern "C" {
#endif

    // CFFI START INCLUDE

    /* note internally some of these methods return const values (check the class definitions).  When we use them from python, no object is ever const.
       Hence, in this api a copy of the object is always returned. */

    void initK273(int console, const char* filename);

    // BaseState operations:
    boolean BaseState__get(BaseState*, int index);
    void BaseState__set(BaseState*, int index, boolean value);
    long BaseState__hashCode(BaseState*);
    boolean BaseState__equals(BaseState*, BaseState* other);
    void BaseState__assign(BaseState*, BaseState* from);
    int BaseState__len(BaseState*);
    void BaseState__deleteBaseState(BaseState*);

    // Create a state machine
    StateMachine* createStateMachine(int role_count, int num_bases, int num_transitions, int num_components, int num_ouputs, int topological_size);
    StateMachine* createGoallessStateMachine(int role_count, StateMachine*, StateMachine*);

    CombinedSM* createCombinedStateMachine(int role_count);
    void CombinedStateMachine__setGoalStateMachine(CombinedSM*, StateMachine* sm);
    void CombinedStateMachine__setControlStateMachine(CombinedSM*, int control_index, int control_cid, StateMachine* sm);

    // StateMachine initialisation:
    void StateMachine__setInitialState(StateMachine*, BaseState* intial_state);

    // Duplicate a statemachine
    StateMachine* StateMachine__dupe(StateMachine*);

    // Delete underlying statemachine
    void StateMachine__delete(StateMachine*);


    // StateMachine interface:
    BaseState* StateMachine__newBaseState(StateMachine*);

    void StateMachine__updateBases(StateMachine*, BaseState* bs);
    LegalState* StateMachine__getLegalState(StateMachine*, int role_index);

    const char* StateMachine__getGDL(StateMachine*, int index);
    const char* StateMachine__legalToMove(StateMachine*, int role_index, int choice);

    JointMove* StateMachine__getJointMove(StateMachine*);
    boolean StateMachine__isTerminal(StateMachine*);
    void StateMachine__nextState(StateMachine*, JointMove* move, BaseState* bs);
    int StateMachine__getGoalValue(StateMachine*, int role_index);

    void StateMachine__getCurrentState(StateMachine*, BaseState* bs);

    void StateMachine__reset(StateMachine*);

    int LegalState__getCount(LegalState*);
    int LegalState__getLegal(LegalState*, int index);

    int JointMove__get(JointMove*, int role_index);
    void JointMove__set(JointMove*, int role_index, int value);


    PlayerBase* Player__createRandomPlayer(StateMachine*, int our_role_index);
    PlayerBase* Player__createLegalPlayer(StateMachine*, int our_role_index);

    // pass everything in
    PlayerBase* Player__createSimpleMCTSPlayer(void* _sm, int our_role_index,
                                               boolean skip_single_moves,
                                               double max_tree_search_time,
                                               long max_memory,
                                               long max_tree_playout_iterations,
                                               int max_number_of_nodes,
                                               double ucb_constant,
                                               int select_random_move_count,
                                               int dump_depth,
                                               double next_time);

    void PlayerBase__cleanup(PlayerBase*);
    void PlayerBase__onMetaGaming(PlayerBase*, double end_time);
    const char* PlayerBase__beforeApplyInfo(PlayerBase*);
    void PlayerBase__onApplyMove(PlayerBase*, JointMove*);
    int PlayerBase__onNextMove(PlayerBase*, double end_time);


    // DepthChargeTest operations:
    DepthChargeTest* DepthChargeTest__create(StateMachine*);
    void DepthChargeTest__doRollouts(DepthChargeTest*, int seconds);
    int DepthChargeTest__getResult(DepthChargeTest*, int index);
    void DepthChargeTest__delete(DepthChargeTest*);

    void Log_verbose(const char*);
    void Log_debug(const char*);
    void Log_info(const char*);
    void Log_warning(const char*);
    void Log_error(const char*);
    void Log_critical(const char*);

    StateMachine* createStateMachineFromJSON(const char* msg, int size);

    // CFFI END INCLUDE

#ifdef __cplusplus
}
#endif

#undef StateMachine
#undef BaseState
#undef LegalState
#undef JointMove
#undef boolean
#undef ComponentType
#undef CombinedStateMachine
#undef PlayerBase
#undef DepthChargeTest
