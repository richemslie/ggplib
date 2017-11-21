
INCLUDE_PATH = -I ./ -I /usr/include/jsoncpp
LIB_PATH = ./

AR = ar
RM = rm -f
CPP = g++

CFLAGS = -MMD -MP -g -Wall -Werror -Woverloaded-virtual -Wnon-virtual-dtor -O3 -fPIC -fomit-frame-pointer -std=c++11
LDFLAGS = -g -MMD -MP -Wall -Werror -Woverloaded-virtual -Wnon-virtual-dtor -O3 -fomit-frame-pointer -std=c++11


# not part of gpplib...  but include until we release k273
SRCS += k273/exception.cpp k273/logging.cpp k273/util.cpp k273/strutils.cpp k273/stacktrace.cpp k273/json.cpp

SRCS += statemachine/basestate.cpp statemachine/propagate.cpp statemachine/combined.cpp
SRCS += player/node.cpp player/rollout.cpp

SRCS += example_players/randomplayer.cpp example_players/legalplayer.cpp example_players/simplemcts.cpp

SRCS += perf_test.cpp interface.cpp

CORE_OBJS = $(patsubst %.cpp, %.o, $(SRCS))
OBJS := $(CORE_OBJS)
DEPS=$(SRCS:.cpp=.d)

# Top level
all: $(OBJS) libggplib_cpp.so

fresh : clean all

# Compiles
libggplib_cpp.so: $(OBJS)
	$(CPP) -shared $(CORE_OBJS) $(LDFLAGS) -L $(LIB_PATH) -pthread -lrt -ljsoncpp -o libggplib_cpp.so

%.o : %.cpp
	$(CPP) $(INCLUDE_PATH) $(CFLAGS) -c -o $@ $<

# Cleans
clean :
	$(RM) $(OBJS) $(DEPS)

realclean : clean
	$(RM) *.so *.log core*

-include $(DEPS)
.PHONY: all fresh clean realclean


