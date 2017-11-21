#include "k273/json.h"
#include "k273/strutils.h"
#include "k273/exception.h"

#include <json/json.h>
#include <json/reader.h>

#include <memory>
#include <string>

using namespace K273;

///////////////////////////////////////////////////////////////////////////////

struct JsonValue::Data {
    Data(const Json::Value& v) :
        value(v) {
    }

    const Json::Value value;
};

///////////////////////////////////////////////////////////////////////////////

JsonValue JsonValue::parseJson(const char* buf, int size) {
    Json::Value root;
    Json::Reader reader;
    reader.parse(buf, buf + size, root);
    JsonValue res = JsonValue(std::make_shared <Data> (root), "root");

    ASSERT (res.isDict());
    return res;
}

///////////////////////////////////////////////////////////////////////////////

JsonValue::JsonValue(std::shared_ptr<const Data> data, const std::string& key) :
    data(data),
    keyed_from(key) {
    ASSERT_MSG (!this->data->value.isNull(),
                K273::fmtString("value is null (keyed %s)",
                                this->keyed_from.c_str()));
}

JsonValue JsonValue::operator[](const std::string& key) const  {
    ASSERT_MSG (this->isDict(),
                K273::fmtString("value is not dictionary (keyed %s)",
                                this->keyed_from.c_str()));

    return JsonValue(std::make_shared <const Data> (this->data->value[key]),
                     key);
}

bool JsonValue::isArray() const {
    return this->data->value.isArray();
}

bool JsonValue::isDict() const {
    return this->data->value.isObject();
}

bool JsonValue::isInt() const {
    return this->data->value.isInt();
}

bool JsonValue::isLong() const {
    return this->data->value.isInt64();
}

bool JsonValue::isBool() const {
    return this->data->value.isBool();
}

bool JsonValue::isString() const {
    return this->data->value.isString();
}

bool JsonValue::isDouble() const {
    return this->data->value.isDouble();
}

///////////////////////////////////////////////////////////////////////////////

int JsonValue::asInt() const {
    ASSERT_MSG (this->isInt(),
                K273::fmtString("value is not int (keyed %s)",
                                this->keyed_from.c_str()));
    return this->data->value.asInt();
}

long JsonValue::asLong() const {
    ASSERT_MSG (this->isLong(),
                K273::fmtString("value is not long (keyed %s)",
                                this->keyed_from.c_str()));
    return this->data->value.asInt64();
}

bool JsonValue::asBool() const {
    ASSERT_MSG (this->isBool(),
                K273::fmtString("value is not bool (keyed %s)",
                                this->keyed_from.c_str()));
    return this->data->value.asBool();
}

std::string JsonValue::asString() const {
    ASSERT_MSG (this->isString(),
                K273::fmtString("value is not string (keyed %s)",
                                this->keyed_from.c_str()));
    return this->data->value.asString();
}

double JsonValue::asDouble() const {
    ASSERT_MSG (this->isDouble(),
                K273::fmtString("value is not double (keyed %s)",
                                this->keyed_from.c_str()));
    return this->data->value.asDouble();
}

///////////////////////////////////////////////////////////////////////////////

JsonValue JsonValue::operator[](int index) const  {
    ASSERT_MSG (this->isArray(),
                K273::fmtString("value is not array (keyed %s)",
                                this->keyed_from.c_str()));

    return JsonValue(std::make_shared <const Data> (this->data->value[index]),
                     K273::fmtString("idx #%d", index));
}

JsonValue::JsonValueIter JsonValue::begin() const {
    ASSERT_MSG (this->isArray(),
                K273::fmtString("value is not array (keyed %s)",
                                this->keyed_from.c_str()));

    return JsonValue::JsonValueIter(this->data, 0);
}

JsonValue::JsonValueIter JsonValue::end() const {
    ASSERT_MSG (this->isArray(),
                K273::fmtString("value is not array (keyed %s)",
                                this->keyed_from.c_str()));

    return JsonValue::JsonValueIter(this->data, this->data->value.size());
}

JsonValue JsonValue::JsonValueIter::operator*() const {
    Json::Value value = this->data->value[this->pos];
    return JsonValue(std::make_shared <const Data> (value),
                     K273::fmtString("iter pos #%d", this->pos));
}
