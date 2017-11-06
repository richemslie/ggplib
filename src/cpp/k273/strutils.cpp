// std includes
#include <cstring>
#include <stdarg.h>

// local includes
#include "exception.h"
#include "strutils.h"

///////////////////////////////////////////////////////////////////////////////

using namespace K273;
using namespace std;

///////////////////////////////////////////////////////////////////////////////

string K273::fmtString(const char *fmt, ...) {
    thread_local char buf[4096];

    bool malloced = false;
    char* pt_fmted = buf;

    va_list args;
    va_start(args, fmt);

    int res;
    res = ::vsnprintf(pt_fmted, 4096, fmt, args);
    if (res < 0) {
        /* shouldnt happen - well not on a os/x ... */
        va_end(args);
        throw Exception("vsnprintf failed");

    } else if (res > 4096) {
        /* not enough room, we'll just malloc it... should be special case */
        res = ::vasprintf(&pt_fmted, fmt, args);
        if (res == -1) {
            va_end(args);
            throw Exception("vasprintf failed");
        }

        malloced = true;

    } else {
        /* ensure null terminated (it should be anyways - but just in case some
           implementions dont) */
        buf[4096-1] = '\0';
    }

    va_end(args);

    string s(pt_fmted);

    if (malloced) {
        ::free(pt_fmted);
    }

    return s;
}


signed int K273::find(const string &input, const string &what) {
    const char* u = strstr(input.c_str(), what.c_str());

    if (u == nullptr) {
        return -1;

    } else {
       int index = u - input.c_str();
       ASSERT (index >= 0);
       return index;
    }
}

string K273::nextToken(const string& input, char token, size_t& start, size_t &end) {
    // iterate over packet contents
    int offset = start;

    if (end > input.size()) {
        return "";
    }

    if (start == end) {
        return "";
    }

    const char* ptbuf = input.c_str();
    while (start < end) {
        char c = *(ptbuf + start);
        start++;

        if (c == token) {
            return string(input.c_str() + offset, start - (offset + 1));
        }
    }

    return string(input.c_str() + offset, start - offset);
}

string K273::charTimes(char c, int length) {
    if (length == 0) {
        return "";
    }

    char buf[128];
    char* pt_buf;
    bool malloced = false;

    if (length < 128) {
        pt_buf = buf;

    } else {
        pt_buf = (char *) ::malloc(length + 1);
        malloced = true;
    }

    ::memset(pt_buf, c, length);
    *(pt_buf + length) = '\0';

    string res(pt_buf);

    if (malloced) {
        ::free(pt_buf);
    }

    return res;
}

string K273::lstrip(const string &input) {
    size_t count = 0;
    const char* pt_buf = input.c_str();
    while (count < input.size() && ::isspace(*pt_buf)) {
        pt_buf++;
        count++;
    }

    if (count == 0) {
        return input;

    } else {
        return string(pt_buf);
    }
}

string K273::rstrip(const string &input) {
    int count = input.size() - 1;
    const char* pt_buf = input.c_str() + count;

    while (count >= 0 && ::isspace(*pt_buf)) {
        pt_buf--;
        count--;
    }

    if (count == ((int) input.size()) - 1) {
        return input;
    } else {
        return string(input.c_str(), count + 1);
    }
}

string K273::strip(const string &input) {
    return rstrip(lstrip(input));
}

string K273::ljust(const string &input, size_t width, char fillchar) {
    if (input.size() >  width) {
        return input;
    }

    int d = width - input.size();
    string res = input;
    res += ::charTimes(fillchar, d);
    return res;
}

string K273::rjust(const string &input, size_t width, char fillchar) {
    if (input.size() > width) {
        return input;
    }

    int d = width - input.size();
    string res = ::charTimes(fillchar, d);
    res += input;
    return res;
}


string K273::lower(const string &input) {
    string s;
    const char* ptbuf = input.c_str();
    for (size_t ii=0; ii<input.size(); ii++, ptbuf++) {
        char c = ::tolower(*ptbuf);
        s += c;
    }

    return s;
}

string K273::upper(const string &input) {
    string s;
    const char* ptbuf = input.c_str();
    for (size_t ii=0; ii<input.size(); ii++, ptbuf++) {
        char c = ::toupper(*ptbuf);
        s += c;
    }

    return s;
}

bool K273::startsWith(const string &input, const string &match) {
    const char* pt_input = input.c_str();
    const char* pt_match = match.c_str();

    for (size_t ii=0; ii<match.size(); ii++, pt_input++, pt_match++) {
        // no input left
        if (ii == input.size()) {
            return false;
        }

        // mismatch
        if (*pt_input != *pt_match) {
            return false;
        }
    }

    // all done, great!
    return true;
}

int K273::toInt(const string &input) {
    char* endptr;
    return ::strtol(input.c_str(), &endptr, 10);
}

unsigned int K273::toUint(const string& input){
    char* endptr = nullptr;
    return static_cast<unsigned int>(::strtol(input.c_str(), &endptr, 10));
}

long long K273::toLongLong(const string &input) {
    char* endptr;
    return ::strtoll(input.c_str(), &endptr, 10);
}

double K273::toDouble(const string &input) {
    return ::atof(input.c_str());
}

bool K273::toBool(const string &input) {
    if (strcasecmp(input.c_str(), "True") == 0) {
        return true;
    } else if (strcasecmp(input.c_str(), "Y") == 0) {
        return true;
    } else if (strcasecmp(input.c_str(), "1") == 0) {
        return true;
    }

    return false;
}

///////////////////////////////////////////////////////////////////////////////

list <string> K273::split(string input, char c) {
    list <string> result;

    bool good = false;
    const char* ptchar = input.c_str();
    const char* ptstart = ptchar;
    for (size_t ii=0; ii<input.size(); ii++, ptchar++) {
        if (*ptchar == c) {
            if (good) {
                result.push_back(string(ptstart, ptchar - ptstart));
                good = false;
            }
        } else {
            if (!good) {
                ptstart = ptchar;
                good = true;
            }
        }
    }

    if (good) {
        result.push_back(string(ptstart, ptchar - ptstart));
    }

    return result;
}
