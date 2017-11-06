#pragma once

#include <cstdint>
#include <cstring>

#include <unordered_map>

namespace GGPLib {
    struct BaseState {
    public:
        // Historical, attempted to different sizes of ArrayType.  In the end it was simplest and
        // most efficient to use bytes.  Leaving typedef as it doesn't make things less clear.
        typedef uint8_t ArrayType;
        static int const ARRAYTYPE_BYTES = 1;
        static int const ARRAYTYPE_BITS = 8;

        static int mallocSize(int num_bases) {
            int bytes_for_bases = num_bases / BaseState::ARRAYTYPE_BYTES + 1;
            return sizeof(BaseState) + bytes_for_bases;
        }

    public:
        // This should override new/delete where the 'data; is part of the allocation
        void init(const int size) {
            this->size = size;
            this->byte_count = size / ARRAYTYPE_BITS + 1;
            std::memset(this->data, 0, this->byte_count * ARRAYTYPE_BYTES);
        }

        const bool get(const int index) const {
            //ASSERT (index < this->size);
            const ArrayType *ptdata = this->data + (index / ARRAYTYPE_BITS);
            int index2 = index % ARRAYTYPE_BITS;
            return *ptdata & (ArrayType(1) << index2);
        }

        const void set(const int index, const bool value) {
            //ASSERT (index < this->size);
            ArrayType *ptdata = this->data + (index / ARRAYTYPE_BITS);
            int index2 = index % ARRAYTYPE_BITS;
            if (value) {
                *ptdata |= (ArrayType(1) << index2);
            } else {
                *ptdata &= ~(ArrayType(1) << index2);
            }
        }

        size_t hashCode() const {
            Hasher hasher;
            return hasher(this);
        }

        bool equals(const BaseState* other) const {
            const ArrayType* pt_data = this->data;
            const ArrayType* pt_other = other->data;
            for (int ii=0; ii<this->byte_count; ii++) {
                if (*pt_data != *pt_other) {
                    return false;
                }
            }

            return true;
        }

        void assign(const BaseState* other) {
            std::memcpy(this->data, other->data, this->byte_count * ARRAYTYPE_BYTES);
        }

    private:
        void calculateHashCode();

        struct Hasher {
            std::size_t operator() (const BaseState* key) const;
        };

        struct Equals {
            bool operator() (const BaseState* a, const BaseState* b) const {
                return a->equals(b);
            }
    };

    public:
        short size;
        short byte_count;
        ArrayType data[0];

    public:
        template <typename V> using HashMap = std::unordered_map <const BaseState*, V, Hasher, Equals>;
    };


};
