#pragma once

// std includes
#include <string>

///////////////////////////////////////////////////////////////////////////////

namespace K273 {

    class Exception {

    public:
        Exception();
        Exception(std::string msg);
        virtual ~Exception();

    public:
        virtual std::string getMessage() const;
        std::string getStacktrace() const;

    protected:
        const std::string message;
        const std::string stacktrace;
    };

    ///////////////////////////////////////////////////////////////////////////
    // general system exceptions (where an error code is set)

    class SysException : public Exception {

    public:
        SysException(std::string msg, int errcode);
        virtual ~SysException();

    public:
        virtual std::string getMessage() const;

        int getErrorCode() const;
        std::string getErrorString() const;

    private:
        const int error_code;
    };

    ///////////////////////////////////////////////////////////////////////////
    // The class for all assertion failures.

    class Assertion : public Exception {
      public:
        Assertion(int on_line, std::string filename, std::string expr);
        Assertion(int on_line, std::string filename, std::string expr, std::string msg);

        virtual ~Assertion();

      public:
        virtual std::string getMessage() const;
        std::string getFile() const;
        int getLine() const;

      private:
        const int on_line;
        const std::string expr;
        const std::string filename;
    };

}

///////////////////////////////////////////////////////////////////////////////
// Assertion macro section

#ifndef K273_ASSERTIONS_OFF

#include "util.h"

#define ASSERT(expr)                                            \
    if (unlikely(!(expr))) {                                    \
        throw K273::Assertion(__LINE__,                         \
                              std::string(__FILE__),            \
                              std::string(#expr));              \
    }

#define ASSERT_MSG(expr, msg)                                   \
    if (unlikely(!(expr))) {                                    \
        throw K273::Assertion(__LINE__,                         \
                              std::string(__FILE__),            \
                              std::string(#expr),               \
                              std::string(msg));                \
    }

#else

#define ASSERT(expr)  // Dummy comment
#define ASSERT_MSG(expr, msg)  // Dummy comment

#endif
