// local includes
#include "logging.h"
#include "exception.h"

// std includes
#include <cerrno>
#include <cstdio>
#include <cstring>
#include <cstring>
#include <algorithm>

#include <stdarg.h>
#include <unistd.h>
#include <sys/time.h>

///////////////////////////////////////////////////////////////////////////////

using namespace std;
using namespace K273;

///////////////////////////////////////////////////////////////////////////////

static Logger& getLogger() {
    static Logger the_logger;
    return the_logger;
}

///////////////////////////////////////////////////////////////////////////////

// Size of the log buffer
const static int LOG_BUFFER_SIZE = 1024 * 8;

// Available log buffer space
const static int LOG_PRINT_SPACE = LOG_BUFFER_SIZE - LogHandlerBase::PrefixLength;

// Common log buffer - thread safe
thread_local char static_log_buffer[LOG_BUFFER_SIZE];


static const char* getLevelName(int level) {
    switch(level) {
    case Logger::LOG_CRITICAL:
        return " [CRITICAL]  ";
    case Logger::LOG_ERROR:
        return " [ERROR   ]  ";
    case Logger::LOG_WARNING:
        return " [WARNING ]  ";
    case Logger::LOG_INFO:
        return " [INFO    ]  ";
    case Logger::LOG_DEBUG:
        return " [DEBUG   ]  ";
    case Logger::LOG_VERBOSE:
        return " [VERBOSE ]  ";
    default:
        return " [NOTSET  ]  ";
    }
}

///////////////////////////////////////////////////////////////////////////////

LogHandlerBase::LogHandlerBase(int level) :
    level(level) {
}

LogHandlerBase::~LogHandlerBase() {
}

void LogHandlerBase::cleanup() {
}

///////////////////////////////////////////////////////////////////////////////

FileLogHandler::FileLogHandler(int level, const string& filename, bool coloured) :
    LogHandlerBase(level),
    coloured(true) {
    this->fp = std::fopen(filename.c_str(), "a");
    if (this->fp == nullptr) {
        throw SysException("Error on opening file", errno);
    }
}

FileLogHandler::~FileLogHandler() {
}

void FileLogHandler::onReport(Logger& logger, string& timestamp, int level, const char* pt_msg) {
    const char* pt_colour_on = nullptr;
    const char* pt_colour_off = nullptr;

    if (this->coloured) {
        switch (level) {
            case Logger::LOG_VERBOSE:
                pt_colour_on = "\033[1;36m";  // CYAN
                pt_colour_off = "\033[0m";
                break;
            case Logger::LOG_DEBUG:
                pt_colour_on = "\033[1;1m";  // BOLD
                pt_colour_off = "\033[0m";
                break;
            case Logger::LOG_INFO:
                pt_colour_on = "\033[1;32m";  // GREEN
                pt_colour_off = "\033[0m";
                break;
            case Logger::LOG_WARNING:
                pt_colour_on = "\033[1;33m";  // YELLOW
                pt_colour_off = "\033[0m";
                break;
            case Logger::LOG_ERROR:
                pt_colour_on = "\033[1;31m";  // RED
                pt_colour_off = "\033[0m";
                break;
            case Logger::LOG_CRITICAL:
                pt_colour_on = "\033[1;35m";  // MAGENTA
                pt_colour_off = "\033[0m";
                break;

            default:
                break;
        }
    }

    if (pt_colour_on != nullptr) {
        std::fwrite(pt_colour_on, std::strlen(pt_colour_on), 1, this->fp);
    }

    std::fwrite(timestamp.c_str(), timestamp.size(), 1, this->fp);
    std::fwrite(pt_msg, std::strlen(pt_msg), 1, this->fp);
    std::fwrite("\n", 1, 1, this->fp);

    if (pt_colour_off != nullptr) {
        std::fwrite(pt_colour_off, strlen(pt_colour_off), 1, this->fp);
    }

    // XXX important: this can kill timing performance if flushing to encrypted filesystems
    //std::fflush(this->fp);
}

void FileLogHandler::cleanup() {
    fclose(this->fp);
}

///////////////////////////////////////////////////////////////////////////////

ConsoleLogHandler::ConsoleLogHandler(int level) :
    LogHandlerBase(level) {
    this->coloured = std::getenv("K273_LOG_NO_COLOR") != nullptr ? false : isatty(fileno(stderr));
}

ConsoleLogHandler::~ConsoleLogHandler() {
}

void ConsoleLogHandler::onReport(Logger& logger, string& timestamp, int level, const char* pt_msg) {
    const char* pt_colour_on = nullptr;
    const char* pt_colour_off = nullptr;

    if (this->coloured) {
        switch (level) {
            case Logger::LOG_VERBOSE:
                pt_colour_on = "\033[1;36m";  // CYAN
                pt_colour_off = "\033[0m";
                break;
            case Logger::LOG_DEBUG:
                pt_colour_on = "\033[1;1m";  // BOLD
                pt_colour_off = "\033[0m";
                break;
            case Logger::LOG_INFO:
                pt_colour_on = "\033[1;32m";  // GREEN
                pt_colour_off = "\033[0m";
                break;
            case Logger::LOG_WARNING:
                pt_colour_on = "\033[1;33m";  // YELLOW
                pt_colour_off = "\033[0m";
                break;
            case Logger::LOG_ERROR:
                pt_colour_on = "\033[1;31m";  // RED
                pt_colour_off = "\033[0m";
                break;
            case Logger::LOG_CRITICAL:
                pt_colour_on = "\033[1;35m";  // MAGENTA
                pt_colour_off = "\033[0m";
                break;

            default:
                break;
        }
    }

    if (pt_colour_on != nullptr) {
        std::fwrite(pt_colour_on, std::strlen(pt_colour_on), 1, stderr);
    }

    std::fwrite(timestamp.c_str(), timestamp.size(), 1, stderr);
    std::fwrite(pt_msg, strlen(pt_msg), 1, stderr);

    if (pt_colour_off != nullptr) {
        std::fwrite(pt_colour_off, strlen(pt_colour_off), 1, stderr);
    }

    std::fwrite("\n", 1, 1, stderr);
}

///////////////////////////////////////////////////////////////////////////////

Logger::Logger() :
    seconds(0),
    useconds(0),
    update_timestamp(true),
    file_handler(nullptr),
    console_handler(nullptr) {
}

Logger::~Logger() {
    this->cleanup();
}

void Logger::fileLogging(const std::string& filename, int level) {
    if (this->file_handler != nullptr) {
        this->removeHandler(this->file_handler);
        this->file_handler = nullptr;
    }

    this->file_handler = new FileLogHandler(level, filename, true);
    this->addHandler(this->file_handler);
}

void Logger::consoleLogging(int level) {
    if (this->console_handler != nullptr) {
        this->removeHandler(this->console_handler);
        this->console_handler = nullptr;
    }

    this->console_handler = new ConsoleLogHandler(level);
    this->addHandler(this->console_handler);
}

void Logger::addHandler(LogHandlerBase* pt_handle) {
    std::lock_guard<std::mutex> lk(this->mutex);
    this->handlers.push_back(pt_handle);
}

void Logger::removeHandler(LogHandlerBase* pt_handle) {
    std::lock_guard<std::mutex> lk(this->mutex);
    auto iter = std::find(this->handlers.begin(), this->handlers.end(), pt_handle);
    if (iter != this->handlers.end()) {
        this->handlers.erase(iter);

        LogHandlerBase* h = *iter;
        h->cleanup();
        delete h;
    }
}

void Logger::cleanup() {
    // cleans up all the handlers, then deletes them
    for (auto h : this->handlers) {
        h->cleanup();
    }

    for (auto h : this->handlers) {
        delete h;
    }

    this->handlers.clear();
}

void Logger::makeLog(int level, const char* fmt, va_list args) {
    std::lock_guard<std::mutex> lk(this->mutex);

     // copy level name
    memcpy(static_log_buffer, ::getLevelName(level), LogHandlerBase::PrefixLength);

     // where we can print
    char* ptr = static_log_buffer + LogHandlerBase::PrefixLength;
    int res = vsnprintf(ptr, LOG_PRINT_SPACE, fmt, args);

    if (res < 0) {
         // only on OSX
        throw Exception("vsnprintf failed");
    }

     // convert to unsigned
    size_t printed = res;

    if (printed >= LOG_PRINT_SPACE) {
         // trancated message
        ptr[LOG_PRINT_SPACE - 1] = '\0';
    }

     // print from the beginning
    this->doLog(level, static_log_buffer);
}

void Logger::makeLog(int level, const string& msg) {
    std::lock_guard<std::mutex> lk(this->mutex);

     // copy level name
    memcpy(static_log_buffer, ::getLevelName(level), LogHandlerBase::PrefixLength);

    // where we can print
    char* ptr = static_log_buffer + LogHandlerBase::PrefixLength;
    size_t len = msg.size();

    if (len >= LOG_PRINT_SPACE) {
        // trancated message
        len = LOG_PRINT_SPACE - 1;
    }

    // raw copy
    memcpy(ptr, msg.c_str(), len);

    // zero-terminate
    ptr[len] = '\0';

    // print from the beginning
    this->doLog(level, static_log_buffer);
}

void Logger::doLog(int level, const char* pt_msg) {
    // XXX this could easily be reduced to one static buffer and no strings

    bool do_log_this_time = false;
    for (auto h : this->handlers) {
        if (level <= h->level) {
            do_log_this_time = true;
            break;
        }
    }

    if (!do_log_this_time) {
        return;
    }

    timespec now;
    ::clock_gettime(CLOCK_REALTIME, &now);
    if (this->seconds != now.tv_sec) {
        struct tm ct;
        memset(&ct, 0, sizeof(struct tm));

        localtime_r(&now.tv_sec, &ct); // XXX check this?

        char seconds_buf[32];
        seconds_buf[31] = '\0';
        if (std::strftime(seconds_buf, 32, "%Y-%m-%d %H:%M:%S", &ct) == 0) {
            throw SysException("strftime() failed", errno);
        }

        this->seconds_str = (char*) seconds_buf;
        this->seconds = now.tv_sec;
        this->update_timestamp = true;
    }

    // rounds down
    int usecs = now.tv_nsec / 1000L;

    if (this->useconds != usecs) {
        this->useconds = usecs;
        this->update_timestamp = true;
    }

    if (this->update_timestamp) {
        // actually 10000 of a second - we'll need the resolution
        char tmp_buf[28];

        //XXX assert ?
        ASSERT (snprintf(tmp_buf, 28, "%s,%06u", this->seconds_str.c_str(), usecs) <= 28);
        this->timestamp_str = (char* ) tmp_buf;
        this->update_timestamp = false;
    }

    for (auto h : this->handlers) {
        if (level <= h->level) {
            h->onReport(*this, this->timestamp_str, level, pt_msg);
        }
    }
}

///////////////////////////////////////////////////////////////////////////////

void K273::loggerSetup(const string& filename, int console_level) {
    ::getLogger().fileLogging(filename);
    ::getLogger().consoleLogging(console_level);

    l_info("K273::loggerSetup() done.");
}

void K273::addLogHandler(LogHandlerBase* handler) {
    ::getLogger().addHandler(handler);
}

void K273::removeLogHandler(LogHandlerBase* handler) {
    ::getLogger().removeHandler(handler);
}

///////////////////////////////////////////////////////////////////////////////

void K273::l_critical(const char* fmt, ...) {
    va_list args;
    va_start(args, fmt);
    ::getLogger().makeLog(Logger::LOG_CRITICAL, fmt, args);
    va_end(args);
}

void K273::l_critical(const string& msg) {
    ::getLogger().makeLog(Logger::LOG_CRITICAL, msg);
}

void K273::l_error(const char* fmt, ...) {
    va_list args;
    va_start(args, fmt);
    ::getLogger().makeLog(Logger::LOG_ERROR, fmt, args);
    va_end(args);
}

void K273::l_error(const string& msg) {
    ::getLogger().makeLog(Logger::LOG_ERROR, msg);
}

void K273::l_warning(const char* fmt, ...) {
    va_list args;
    va_start(args, fmt);
    ::getLogger().makeLog(Logger::LOG_WARNING, fmt, args);
    va_end(args);
}

void K273::l_warning(const string& msg) {
    ::getLogger().makeLog(Logger::LOG_WARNING, msg);
}

void K273::l_info(const char* fmt, ...) {
    va_list args;
    va_start(args, fmt);
    ::getLogger().makeLog(Logger::LOG_INFO, fmt, args);
    va_end(args);
}

void K273::l_info(const string& msg) {
    ::getLogger().makeLog(Logger::LOG_INFO, msg);
}

void K273::l_debug(const char* fmt, ...) {
    va_list args;
    va_start(args, fmt);
    ::getLogger().makeLog(Logger::LOG_DEBUG, fmt, args);
    va_end(args);
}

void K273::l_debug(const string& msg) {
    ::getLogger().makeLog(Logger::LOG_DEBUG, msg);
}

void K273::l_verbose(const char* fmt, ...) {
    va_list args;
    va_start(args, fmt);
    ::getLogger().makeLog(Logger::LOG_VERBOSE, fmt, args);
    va_end(args);
}

void K273::l_verbose(const string& msg) {
    ::getLogger().makeLog(Logger::LOG_VERBOSE, msg);
}
