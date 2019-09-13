include $(K273_PATH)/src/cpp/Makefile.in

LIBS = -L $(K273_PATH)/src/cpp/k273 -lk273

CFLAGS += -fPIC

SRCS += statemachine/basestate.cpp statemachine/propagate.cpp statemachine/combined.cpp
SRCS += player/node.cpp player/rollout.cpp

SRCS += example_players/randomplayer.cpp example_players/legalplayer.cpp example_players/simplemcts.cpp

DRAUGHTS = statemachine/external/draughts
SRCS += $(DRAUGHTS)/board.cpp $(DRAUGHTS)/desc.cpp $(DRAUGHTS)/init.cpp $(DRAUGHTS)/sm.cpp

SRCS += perf_test.cpp interface.cpp

OBJS := $(patsubst %.cpp, %.o, $(SRCS))
DEPS=$(SRCS:.cpp=.d)

# Top level
all: $(OBJS) libggplib_cpp.so

libggplib_cpp.so: $(OBJS)
	$(CPP) -shared $(LDFLAGS) $(OBJS) $(LIBS) -o $@

%.o : %.cpp
	$(CPP) $(INCLUDE_PATHS) -I. $(CFLAGS) -c -o $@ $<

# Cleans
clean :
	$(RM) libggplib_cpp.so $(OBJS) $(DEPS)

-include $(DEPS)
.PHONY: all clean


