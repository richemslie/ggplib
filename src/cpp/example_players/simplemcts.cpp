
#include "simplemcts.h"

#include "player/rollout.h"

#include <k273/util.h>
#include <k273/logging.h>
#include <k273/exception.h>

#include <cmath>
#include <unistd.h>

using namespace K273;
using namespace GGPLib;
using namespace GGPLib::SimpleMcts;

///////////////////////////////////////////////////////////////////////////////

Player::Player(StateMachineInterface* sm, int player_role_index, Config* config) :
    PlayerBase(sm, player_role_index),
    config(config),
    rollout(nullptr),
    static_base_state(nullptr),
    root(nullptr),
    number_of_nodes(0),
    node_allocated_memory(0) {

    StateMachineInterface* dupe_sm = this->sm->dupe();
    this->rollout = new DepthChargeRollout(dupe_sm);
    this->static_base_state = this->sm->newBaseState();

    this->playout_stats.reset();
}

Player::~Player() {
    delete this->rollout;
    free(this->static_base_state);

    if (this->root != nullptr) {
        this->removeNode(this->root);
        this->root = nullptr;
    }

    if (this->number_of_nodes) {
        K273::l_warning("Number of nodes not zero %d", this->number_of_nodes);
    }

    if (this->node_allocated_memory) {
        K273::l_warning("Leaked memory %ld", this->node_allocated_memory);
    }

    delete this->config;
}

///////////////////////////////////////////////////////////////////////////////

Node* Player::createNode(const BaseState* bs) {
    // update the statemachine
    this->sm->updateBases(bs);

    const int role_count = this->sm->getRoleCount();
    Node* new_node = Node::create(role_count,
                                  this->our_role_index,
                                  0,  // ucb_constant not used
                                  bs,
                                  this->sm);

    this->number_of_nodes++;
    this->node_allocated_memory += new_node->allocated_size;

    if (new_node->is_finalised) {
        for (int ii=0; ii<role_count; ii++) {
            int score = this->sm->getGoalValue(ii);
            new_node->setScore(ii, score / 100.0);
        }
    }

    return new_node;
}

void Player::removeNode(Node* node) {
    // recursively remove children
    int role_count = this->sm->getRoleCount();

    for (int ii=0; ii<node->num_children; ii++) {
        NodeChild* child = node->getNodeChild(role_count, ii);
        if (child->to_node != nullptr) {
            this->removeNode(child->to_node);
        }

        child->to_node = nullptr;
    }

    this->node_allocated_memory -= node->allocated_size;

    free(node);
    this->number_of_nodes--;
}

///////////////////////////////////////////////////////////////////////////////

void Player::selectChild(Node* node) {
    ASSERT (!node->is_finalised);

    const int role_count = this->sm->getRoleCount();
    const int lead_role_index = node->lead_role_index;
    ASSERT (lead_role_index >= 0);

    double best_explore_score = -1000000;

    NodeChild* best_child = nullptr;

    const int random_counts = std::max(this->config->select_random_move_count, node->num_children / 4);

    for (int ii=0; ii<node->num_children; ii++) {
        NodeChild* c = node->getNodeChild(role_count, ii);

        const double sqrt_visits = c->to_node != nullptr ? ::sqrt(c->to_node->visits + 1) : 1;
        const double exploration_bonus = this->config->ucb_constant * node->sqrt_log_visits / sqrt_visits;

        double search_score;
        if (node->visits > random_counts && c->to_node != nullptr) {
            search_score = c->to_node->getScore(lead_role_index);

        } else {
            // max score
            search_score = 1.0;

            // add some randomness
            const double rand_size = 100 * (this->random.getWithMax(1000) + 1);
            search_score = 1.0 + 1.0 / rand_size;
        }

        const double score = search_score + exploration_bonus;

        if (score > best_explore_score) {
            best_explore_score = score;
            best_child = c;
        }
    }

    this->path.add(node, best_child);
}

void Player::backPropagate(double* new_scores) {
    const int role_count = this->sm->getRoleCount();
    const int start_index = this->path.size() - 1;

    // back propagation:
    for (int index=start_index; index >= 0; index--) {
        Node* node = this->path.get(index)->node;

        for (int ii=0; ii<role_count; ii++) {
            double score = (node->visits * node->getScore(ii) + new_scores[ii]) / (node->visits + 1.0);
            node->setScore(ii, score);
        }

        node->visits++;
        node->sqrt_log_visits = std::sqrt(std::log((double) node->visits + 1.0));
    }
}

int Player::treePlayout() {
    int tree_playout_depth = 0;

    this->path.clear();

    Node* current = this->root;
    while (true) {
        ASSERT (current != nullptr);

        // End of the road
        if (current->is_finalised) {
            this->path.add(current);
            break;
        }

        // Choose selection
        this->selectChild(current);
        tree_playout_depth++;

        // get the next node
        current = this->path.getNextNode();

        // if does not exist, then create the it
        if (current == nullptr) {
            auto* last = this->path.getLast();

            // ask the statemachine for the next state
            this->sm->updateBases(last->node->getBaseState());
            this->sm->nextState(&last->selection->move, this->static_base_state);

            // create node...
            last->selection->to_node = this->createNode(this->static_base_state);

            // add the newly created node to the path (so can backPropagate)
            this->path.add(last->selection->to_node);

            break;
        }
    }

    return tree_playout_depth;
}

///////////////////////////////////////////////////////////////////////////////

NodeChild* Player::chooseBest(Node* node) {
    // no child in finalised nodes
    if (node->num_children == 0) {
        ASSERT (node->is_finalised);
        return nullptr;
    }

    const int role_count = this->sm->getRoleCount();

    int best_visits = -1;
    NodeChild* selection = nullptr;

    for (int ii=0; ii<node->num_children; ii++) {
        NodeChild* c = node->getNodeChild(role_count, ii);

        if (c->to_node != nullptr && c->to_node->visits > best_visits) {
            best_visits = c->to_node->visits;
            selection = c;
        }
    }

    // failsafe - random
    if (selection == nullptr) {
        selection = node->getNodeChild(role_count, this->random.getWithMax(node->num_children));
    }

    return selection;
}

void Player::logDebug(double total_time_seconds) {
    double allocated_megs = this->node_allocated_memory / (1024.0 * 1024.0);
    double av_node_size = this->node_allocated_memory / (double) this->number_of_nodes;

    K273::l_info("------");
    K273::l_info("Did %d (%.1f p/sec) tree-playouts, %d rollouts",
                 this->playout_stats.tree_playouts,
                 this->playout_stats.tree_playouts / total_time_seconds,
                 this->playout_stats.rollouts);

    K273::l_info("Nodes: %d / memory allocated: %.2fM / node size: %.1f",
                 this->number_of_nodes,
                 allocated_megs,
                 av_node_size);

    double pct_search = this->playout_stats.tree_playout_accumulative_time / total_time_seconds;
    double pct_backprop = this->playout_stats.back_propagate_accumulative_time / total_time_seconds;
    double pct_rollout_busy = this->playout_stats.rollout_accumulative_time / total_time_seconds;
    double average_depth = this->playout_stats.total_tree_playout_depth / (double) this->playout_stats.tree_playouts;

    K273::l_info("Pct search:%.2f / back:%.2f / rollout:%.2f / search depth:%.1f",
                 pct_search,
                 pct_backprop,
                 pct_rollout_busy,
                 average_depth);

    K273::l_info("------");

    Node* cur = this->root;
    for (int ii=0; ii<this->config->dump_depth; ii++) {
        std::string indent = "";
        for (int jj=ii-1; jj>=0; jj--) {
            if (jj > 0) {
                indent += "    ";
            } else {
                indent += ".   ";
            }
        }

        NodeChild* next_winner = this->chooseBest(cur);
        if (next_winner == nullptr) {
            break;
        }

        Node::dumpNode(cur, next_winner, indent, this->sm);
        cur = next_winner->to_node;
        if (cur == nullptr) {
            break;
        }
    }
}

///////////////////////////////////////////////////////////////////////////////

void Player::onMetaGaming(double end_time) {
    double enter_time = get_time();
    K273::l_info("entering onMetaGaming() with %.1f seconds", end_time - enter_time);

    // just builds tree for a bit
    this->onNextMove(end_time - 1);
}

void Player::onApplyMove(JointMove* last_move) {

    this->game_depth++;
    K273::l_info("SimpleMCTS: game depth %d", this->game_depth);

    int number_of_nodes_before = this->number_of_nodes;

    // get a new root, and cleanup orphaned branches from tree
    int role_count = this->sm->getRoleCount();
    if (this->root != nullptr) {
        NodeChild* found_child = nullptr;

        // find the child in the root
        for (int ii=0; ii<this->root->num_children; ii++) {
            NodeChild* child = this->root->getNodeChild(role_count, ii);
            if (child->move.equals(last_move)) {
                K273::l_debug("Found next state");
                found_child = child;
                break;
            }
        }

        if (found_child != nullptr) {
            // warning, may be still be null
            Node* new_root = found_child->to_node;
            K273::l_debug("Removing root node");

            // removeNode() is recursive, we must disconnect it from the tree here before calling
            found_child->to_node = nullptr;
            this->removeNode(this->root);

            this->root = new_root;

        } else {
            K273::l_error("weird, did not find move in tree root");
            this->removeNode(this->root);
            this->root = nullptr;
        }
    }

    K273::l_info("deleted %d nodes", number_of_nodes_before - this->number_of_nodes);
}

int Player::onNextMove(double end_time) {
    const int role_count = this->sm->getRoleCount();

    if (this->config->skip_single_moves) {
        LegalState* ls = this->sm->getLegalState(this->our_role_index);
        if (ls->getCount() == 1) {
            int choice = ls->getLegal(0);
            K273::l_info("Only one move - playing it : %s", this->sm->legalToMove(this->our_role_index, choice));
            return choice;
        }
    }

    double enter_time = get_time();
    K273::l_debug("entering onNextMove() with %.1f seconds", end_time - enter_time);

    if (this->config->max_tree_search_time > 0 && enter_time + this->config->max_tree_search_time < end_time) {
        end_time = enter_time + this->config->max_tree_search_time;
    }

    K273::l_debug("searching for %.1f seconds", end_time - enter_time);

    // we create a node for the root (if does not exist already)
    if (this->root == nullptr) {
        K273::l_info("Creating root node");
        this->root = this->createNode(this->sm->getCurrentState());

    } else {
        K273::l_info("Root existing with %d nodes", this->number_of_nodes);
    }

    K273::l_info("Doing playouts...");

    // times (for debugging)
    this->playout_stats.reset();

    double next_time = enter_time + this->config->next_time;
    double next_check_time = enter_time + 0.5;

    while (true) {
        // check elapsed time
        double float_time = get_time();
        if (float_time > end_time) {
            break;

        } else if (float_time > next_time) {

            // get best score for root node and log some minor information
            NodeChild* best = this->chooseBest(this->root);
            if (best != nullptr && best->to_node != nullptr) {
                double our_score = best->to_node->getScore(this->our_role_index);
                int choice = best->move.get(this->our_role_index);

                double average_depth = this->playout_stats.total_tree_playout_depth / (double) this->playout_stats.tree_playouts;


                K273::l_debug("#nodes %d, #playouts %d, av depth: %.2f, score: %.2f, move: %s",
                              this->number_of_nodes,
                              this->playout_stats.tree_playouts,
                              average_depth,
                              our_score,
                              this->sm->legalToMove(this->our_role_index, choice));
            }

            next_time = float_time + this->config->next_time;

        } else if (float_time > next_check_time) {
            // early breaking checks

            if (this->playout_stats.tree_playouts > this->config->max_tree_playout_iterations) {
                K273::l_warning("Breaking early since max tree playout iterations.");
                break;
            }

            if (this->node_allocated_memory > this->config->max_memory) {
                K273::l_warning("Breaking since exceeded maximum memory constraint.");
                break;
            }

            if (this->number_of_nodes > this->config->max_number_of_nodes) {
                K273::l_warning("Breaking since exceeded maximum number of nodes.");
                break;
            }

            next_check_time = float_time + 0.5;
        }

        // do tree playout and gather stats
        const double tree_playout_start_time = get_time();
        const int tree_playout_depth = this->treePlayout();
        this->playout_stats.total_tree_playout_depth += tree_playout_depth;
        this->playout_stats.tree_playouts++;
        this->playout_stats.tree_playout_accumulative_time += get_time() - tree_playout_start_time;

        // can we break early - since game finalised?
        if (tree_playout_depth == 0) {
            K273::l_warning("Breaking early from tree playouts since root is in terminal state");
            break;
        }

        ASSERT (this->path.size() >= 1);
        Node* last = this->path.getLast()->node;
        ASSERT (last != nullptr);

        // get the scores
        double new_scores[role_count];

        // perform a rollout from current node? (to obtain scores):
        if (!last->is_finalised) {

            // do the rollout and gather stats
            const double rollout_start_time = get_time();
            this->rollout->doRollout(last->getBaseState());
            this->playout_stats.rollout_accumulative_time += get_time() - rollout_start_time;
            this->playout_stats.rollouts++;

            for (int ii=0; ii<role_count; ii++) {
                new_scores[ii] = this->rollout->getScore(ii) / 100.0;
            }

        } else {
            // simply set score from the finalised node
            for (int ii=0; ii<role_count; ii++) {
                new_scores[ii] = last->getScore(ii);
            }
        }

        const double back_propagate_start_time = get_time();
        this->backPropagate(new_scores);
        this->playout_stats.back_propagate_accumulative_time += get_time() - back_propagate_start_time;
    }

    // dump bunch of information to log file
    this->logDebug(get_time() - enter_time);

    // Choose best move from root (with the most visits)
    NodeChild* winner = this->chooseBest(this->root);
    ASSERT (winner != nullptr);

    // and return choice
    int choice = winner->move.get(this->our_role_index);
    K273::l_info("Selected: %s", this->sm->legalToMove(this->our_role_index, choice));
    return choice;
}
