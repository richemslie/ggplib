#include <memory>
#include <string>

namespace K273 {

    /* simple read only wrapper around jsoncpp that asserts values exist and are valid
       values... rather than silently failing */
    class JsonValue {
    private:
        // internal forward
        struct Data;
        explicit JsonValue(std::shared_ptr<const Data>, const std::string& key);

    public:
        // to parse from buffer
        static JsonValue parseJson(const char* buf, int size);

        class JsonValueIter {
        public:
            JsonValueIter(std::shared_ptr<const Data> d, int pos) :
                data(d),
                pos(pos) {
            }

            bool operator != (const JsonValueIter& other) const {
                return this->pos != other.pos;
            }

            JsonValue operator*() const;

            void operator++() {
                this->pos++;
            }

        private:
            std::shared_ptr<const Data> data;
            int pos;
        };

    public:
        // default copying/assignment
        JsonValue(const JsonValue&) = default;
        JsonValue& operator= (const JsonValue&) = default;

        // checks:
        bool isArray() const;
        bool isDict() const;
        bool isInt() const;
        bool isLong() const;
        bool isBool() const;
        bool isString() const;
        bool isDouble() const;

        // for dictionary/objects only
        JsonValue operator[](const std::string& key) const;

        int asInt() const;
        long asLong() const;
        bool asBool() const;
        std::string asString() const;
        double asDouble() const;

        // for arrays only
        JsonValue operator[](int index) const;
        JsonValueIter begin() const;
        JsonValueIter end() const;

    private:
        // hide underlying json library
        std::shared_ptr<const Data> data;

        const std::string keyed_from;
    };








}
