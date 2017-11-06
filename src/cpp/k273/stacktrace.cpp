/* Borrowed code for stack traces from
   http://tombarta.wordpress.com/2008/08/01/c-stack-traces-with-gcc */

// local includes
#include "stacktrace.h"
#include "strutils.h"

// std includes
#include <cstring>
#include <string>
#include <cxxabi.h>
#include <execinfo.h>

///////////////////////////////////////////////////////////////////////////////

std::string K273::getStackTrace() {
    const size_t max_depth = 100;
    size_t stack_depth;
    void* stack_addrs[max_depth];
    char** stack_strings;

    stack_depth = ::backtrace(stack_addrs, max_depth);
    stack_strings = ::backtrace_symbols(stack_addrs, stack_depth);

    std::string trace;

    for (size_t i=1; i<stack_depth; i++) {
        // just a guess, template names will go much wider
        size_t sz = 200;
        char *function = (char *) ::malloc(sz);
        char *begin = 0, *end = 0;

        // find the parentheses and address offset surrounding the mangled name
        for (char *j = stack_strings[i]; *j; ++j) {
            if (*j == '(') {
                begin = j;
            }
            else if (*j == '+') {
                end = j;
            }
        }

        if (begin && end) {
            *begin++ = '\0';
            *end = '\0';

            // found our mangled name, now in [begin, end)
            int status;
            char *ret = abi::__cxa_demangle(begin, function, &sz, &status);
            if (ret) {
                // return value may be a realloc() of the input
                function = ret;

            } else {
                // demangling failed, just pretend it's a C function with no args
                std::strncpy(function, begin, sz);
                std::strncat(function, "()", sz);
                function[sz-1] = '\0';
            }

            trace += K273::fmtString("    %s  :  %s\n", stack_strings[i], function);

        } else {
            // didn't find the mangled name, just print the whole line
            trace += K273::fmtString("    %s\n", stack_strings[i]);
        }

        ::free(function);
    }

     // malloc()ed by backtrace_symbols
    ::free(stack_strings);
    return trace;
}
