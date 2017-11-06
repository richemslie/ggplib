#pragma once

namespace GGPLib {

    class LegalState {

    public:
        LegalState(int capacity=0) :
            count(0),
            capacity(0),
            indices(nullptr) {
            if (capacity) {
                this->resize(capacity);
            }
        }

        ~LegalState() {
            if (this->indices != nullptr) {
                delete this->indices;
            }
        }

        void resize(int capacity) {
            if (capacity > this->capacity) {
                if (this->indices != nullptr) {
                    delete this->indices;
                }

                this->indices = new int[capacity];
                this->positions = new int[capacity];
            }

            this->capacity = capacity;
        }

        int getCount() const {
            return this->count;
        }

        int getLegal(int at) const {
            return *(this->indices + at);
        }

        void remove(int value) {
            int tail_pos = this->count - 1;
            int pos = *(this->positions + value);
            if (tail_pos != pos) {
                // swap - to fill the hole
                int value_other = *(this->indices + pos) = *(this->indices + tail_pos);

                // update the position of the moved value
                *(this->positions + value_other) = pos;
            }

            this->count--;
        }

        void insert(int value) {
            int index = this->count;
            *(this->positions + value) = index;
            *(this->indices + index) = value;

            this->count++;
        }

    private:
        int count;

        // This is an index into Components - it is the input
        int capacity;
        int* indices;
        int* positions;
    };
}
