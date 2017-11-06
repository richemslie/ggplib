#pragma once

#include "statemachine/statemachine.h"
#include "statemachine/jointmove.h"
#include "statemachine/basestate.h"

#include <k273/util.h>

#include <atomic>

namespace GGPLib {
    const int LEAD_ROLE_INDEX_SIMULTANEOUS = -1;

    // Forwards
    struct Node;

    struct NodeChild {
        Node* to_node;
        bool unselectable;
        int traversals;
        double inv_sqrt_traversals;

        JointMove move;
    };

    typedef double Score;

    struct Node {
        // actual visits
        int visits;
        double sqrt_log_visits;

        // The initial ucb constant
        double select_ucb_constant;

        // visited count, but not been added back in yet (decremented when applying updates)
        uint16_t inflight_visits;

        // Needed for transpositions and releasing nodes.
        uint16_t ref_count;

        uint16_t num_children;
        uint16_t unselectable_count;

        // whether this node has a finalised scores or not (can also release children if so)
        bool is_finalised;

        // we don't really know which player it really it is for each node, but this is our best guess
        int16_t lead_role_index;

        // prediction of how long to reach a terminal state
        double expected_depth;

        // internal pointer to scores
        uint16_t basestate_ptr_incr;
        uint16_t children_ptr_incr;

        // actual size of this node
        int allocated_size;

        uint8_t data[0];

        Score getScore(int role_index) const {
            const Score* scores = reinterpret_cast<const Score*> (this->data);
            return *(scores + role_index);
        }

        void setScore(int role_index, Score score) {
            Score* scores = reinterpret_cast<Score*> (this->data);
            *(scores + role_index) = score;
        }

        NodeChild* getNodeChild(const int role_count, const int child_index) {
            int node_child_bytes = sizeof(NodeChild) + role_count * sizeof(JointMove::IndexType);
            node_child_bytes = ((node_child_bytes / 4) + 1) * 4;

            uint8_t* mem = this->data;
            mem += this->children_ptr_incr;
            mem += node_child_bytes * child_index;
            return reinterpret_cast<NodeChild*> (mem);
        }

        const NodeChild* getNodeChild(const int role_count, const int child_index) const {
            int node_child_bytes = sizeof(NodeChild) + role_count * sizeof(JointMove::IndexType);
            node_child_bytes = ((node_child_bytes / 4) + 1) * 4;

            const uint8_t* mem = this->data;
            mem += this->children_ptr_incr;
            mem += node_child_bytes * child_index;
            return reinterpret_cast<const NodeChild*> (mem);
        }

        BaseState* getBaseState() {
            uint8_t* mem = this->data;
            mem += this->basestate_ptr_incr;
            return reinterpret_cast<BaseState*> (mem);
        }

        const BaseState* getBaseState() const {
            const uint8_t* mem = this->data;
            mem += this->basestate_ptr_incr;
            return reinterpret_cast<const BaseState*> (mem);
        }

        bool isTerminal() const {
            return this->num_children == 0;
        }

        static Node* create(int role_count,
                            int our_role_index,
                            double select_ucb_constant,
                            const BaseState* base_state,
                            StateMachineInterface* sm);

        static void dumpNode(const Node* node, const NodeChild* highlight,
                             const std::string& indent, StateMachineInterface* sm);
    };

}

