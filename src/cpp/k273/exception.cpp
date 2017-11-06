// local includes
#include "exception.h"
#include "stacktrace.h"
#include "strutils.h"

// std includes
#include <cstdio>
#include <cstdlib>
#include <cstring>
#include <string>

///////////////////////////////////////////////////////////////////////////////

using namespace std;
using namespace K273;

///////////////////////////////////////////////////////////////////////////////

Exception::Exception() :
    stacktrace(K273::getStackTrace()) {
}

Exception::Exception(string msg) :
    message(msg),
    stacktrace(K273::getStackTrace()) {
}

Exception::~Exception() {
}

string Exception::getMessage() const {
    return this->message;
}

string Exception::getStacktrace() const {
    return this->stacktrace;
}

///////////////////////////////////////////////////////////////////////////////

SysException::SysException(string msg, int code) :
    Exception(msg),
    error_code(code) {
}

SysException::~SysException() {
}

string SysException::getMessage() const {
    // XXX why not use fmtString() ?
    string buf = this->message;
    buf += ", error string is \"";
    string s = this->getErrorString();
    buf += s;
    buf += "\"";
    return buf;
}

int SysException::getErrorCode() const {
    return this->error_code;
}

string SysException::getErrorString() const {
    string buf = strerror(this->error_code);
    return buf;
}

///////////////////////////////////////////////////////////////////////////////

Assertion::Assertion(int on_line, string filename, string expr) :
    on_line(on_line),
    expr(expr),
    filename(filename) {
}

Assertion::Assertion(int on_line, string filename, string expr, string msg) :
    Exception(msg),
    on_line(on_line),
    expr(expr),
    filename(filename) {
}

Assertion::~Assertion() {
}

string Assertion::getMessage() const {
    // XXX why not use fmtString() ?

    string buf = "'";
    buf += this->expr;
    buf += "' ";

    buf += "at line ";
    buf += K273::fmtString("%u", this->on_line);
    buf += ", in file \"";
    buf += this->filename;
    buf += "\"";

    if (this->message != "") {
        buf += ", message : \"";
        buf += this->message;
        buf += "\"";

    }

    return buf;
}

string Assertion::getFile() const {
    return this->filename;
}

int Assertion::getLine() const {
    return this->on_line;
}
