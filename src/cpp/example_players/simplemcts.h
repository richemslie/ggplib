#pragma once

#include "player/player.h"

#include "player/node.h"
#include "player/path.h"
#include "player/rollout.h"

#include "statemachine/basestate.h"
#include "statemachine/jointmove.h"
#include "statemachine/statemachine.h"

#include <string>
#include <vector>

namespace GGPLib {
    namespace SimpleMcts {

    struct Config {
        bool skip_single_moves;
        double max_tree_search_time;

        long max_memory;
        long max_tree_playout_iterations;
        int max_number_of_nodes;

        double ucb_constant;

        int select_random_move_count;

        int dump_depth;
        double next_time;
    };

    class Player : public PlayerBase {
    public:
        Player(StateMachineInterface*, int player_role_index, Config*);
        virtual ~Player();

    private:
        Node* createNode(const BaseState* bs);
        void removeNode(Node* n);

        void selectChild(Node* node);

        void backPropagate(double* new_scores);
        int treePlayout();

        NodeChild* chooseBest(Node* node);

        void logDebug(double total_time_seconds);

    public:
        // interface:
        virtual void onMetaGaming(double end_time);

        virtual std::string beforeApplyInfo();

        virtual void onApplyMove(JointMove* move);
        virtual int onNextMove(double end_time);

    private:
        Config* config;

        DepthChargeRollout* rollout;
        BaseState* static_base_state;

        // tree stuff
        Node* root;
        int number_of_nodes;
        long node_allocated_memory;

        Path::Selected path;

        struct PlayoutStats {
            double tree_playout_accumulative_time;
            double rollout_accumulative_time;
            double back_propagate_accumulative_time;

            int total_tree_playout_depth;
            int rollouts;
            int tree_playouts;

            void reset() {
                memset(this, 0, sizeof(PlayoutStats));
            }
        };

        PlayoutStats playout_stats;
        K273::Random random;
    };

    }
}
