#pragma once

// std includes
#include <string>
#include <list>

namespace K273 {

    std::string fmtString(const char* fmt, ...);

    // python: 'x' * 42
    std::string charTimes(char c, int length);

    std::string nextToken(const std::string& input, char token, size_t& start, size_t& end);

    std::string lstrip(const std::string& input);
    std::string rstrip(const std::string& input);
    std::string strip(const std::string& input);

    std::string ljust(const std::string& input, size_t width, char fillchar=' ');
    std::string rjust(const std::string& input, size_t width, char fillchar=' ');

    std::string lower(const std::string& input);
    std::string upper(const std::string& input);

    bool startsWith(const std::string& input, const std::string& match);

    // returns a list of strings - not sure very efficient
    std::list <std::string> split(std::string input, char c=' ');

    int find(const std::string& input, const std::string& what);

    int toInt(const std::string& input);
    unsigned int toUint(const std::string& input);
    long long toLongLong(const std::string& input);
    double toDouble(const std::string& input);
    bool toBool(const std::string& input);

}

