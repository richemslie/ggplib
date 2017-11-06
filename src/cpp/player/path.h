#pragma once

#include "player/node.h"

#include <vector>

namespace GGPLib {
    namespace Path {

        struct Element {
        public:
            Element(Node* n, NodeChild* s, bool e) :
                node(n),
                selection(s),
                exploitation(e) {
            }

        public:
            // The current node.
            Node* node;

            // This is the selection from the current node.
            NodeChild* selection;

            // Indicated if the selection was an exploitation or exploration.
            bool exploitation;
        };

        class Selected {
        public:
            Selected() {
                this->elements.reserve(200);
            }

            ~Selected() {
            }

        public:
            void clear() {
                this->elements.clear();
            }

            void add(Node* n, NodeChild* s=nullptr, bool e=false) {
                this->elements.emplace_back(n, s, e);
            }

            Element* get(int index) {
                return &this->elements[index];
            }

            const Element* get(int index) const {
                return &this->elements[index];
            }

            Element* getLast() {
                return this->get(this->elements.size() - 1);
            }

            const Element* getLast() const {
                return this->get(this->elements.size() - 1);
            }

            Node* getNextNode() const {
                // returns the next node that was selected might be nullptr, if not been created
                return this->getLast()->selection->to_node;
            }

            int size() const {
                return this->elements.size();
            }

        private:
            std::vector <Element> elements;
        };

    }
}
