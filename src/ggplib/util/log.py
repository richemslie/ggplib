__all__ = "initialise verbose debug info warning critical Log".split()


cpp_log = None


def initialise(logname=None):
    if logname is None:
        global cpp_log
        from ggplib.interface import Logging
        cpp_log = Logging()
    else:
        init_basic_python_logging(logname)


def init_basic_python_logging(logname):
    ' use standard python framework for logging '

    # stdlib imports
    import logging

    cpp_log = logging.getLogger('basic logger')
    cpp_log.setLevel(logging.DEBUG)

    # create file handler which logs even debug messages
    fh = logging.FileHandler(logname)
    fh.setLevel(logging.DEBUG)

    ch = logging.StreamHandler()
    ch.setLevel(logging.DEBUG)

    # create formatter and add it to the handlers
    formatter = logging.Formatter('%(asctime)s [%(levelname)-8s]  %(message)')
    fh.setFormatter(formatter)
    ch.setFormatter(formatter)

    cpp_log.addHandler(fh)
    cpp_log.addHandler(ch)


def verbose(msg):
    if cpp_log:
        cpp_log.verbose(msg)
    else:
        print msg


def debug(msg):
    if cpp_log:
        cpp_log.debug(msg)
    else:
        print msg


def info(msg):
    if cpp_log:
        cpp_log.info(msg)
    else:
        print msg


def warning(msg):
    if cpp_log:
        cpp_log.warning(msg)
    else:
        print msg


def error(msg):
    if cpp_log:
        cpp_log.error(msg)
    else:
        print msg


def critical(msg):
    if cpp_log:
        cpp_log.critical(msg)
    else:
        print msg


class LogLevel:
    none = 1
    critical = 2
    error = 3
    warning = 4
    info = 5
    debug = 6
    verbose = 7


class Log:
    ' module level logger '

    def __init__(self, level=LogLevel.verbose):
        self.log_level = level

    def verbose(self, *args):
        if self.log_level >= LogLevel.verbose:
            self.do_log(verbose, (args))

    def debug(self, *args):
        if self.log_level >= LogLevel.debug:
            self.do_log(debug, args)

    def info(self, *args):
        if self.log_level >= LogLevel.info:
            self.do_log(info, args)

    def warning(self, *args):
        if self.log_level >= LogLevel.warning:
            self.do_log(warning, args)

    def error(self, *args):
        if self.log_level >= LogLevel.error:
            self.do_log(error, args)

    def critical(self, *args):
        if self.log_level >= LogLevel.critical:
            self.do_log(critical, args)

    def do_log(self, fn, args):
        msg = " ".join(args)
        fn(msg)

    def __call__(self, *args):
        self.debug(*args)
