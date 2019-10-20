include $(K273_PATH)/src/cpp/Makefile.in

LIBS = -L $(K273_PATH)/src/cpp/k273 -lk273

CFLAGS += -fPIC

SRCS += statemachine/basestate.cpp statemachine/propagate.cpp statemachine/combined.cpp
SRCS += player/node.cpp player/rollout.cpp

SRCS += example_players/randomplayer.cpp example_players/legalplayer.cpp example_players/simplemcts.cpp

DRAUGHTS = statemachine/external/draughts
SRCS += $(DRAUGHTS)/board.cpp $(DRAUGHTS)/desc.cpp $(DRAUGHTS)/init.cpp $(DRAUGHTS)/sm.cpp

BADUK = statemachine/external/baduk
SRCS += $(BADUK)/board.cpp $(BADUK)/desc.cpp $(BADUK)/init.cpp $(BADUK)/sm.cpp

HEX = statemachine/external/hex
SRCS += $(HEX)/desc.cpp $(HEX)/sm.cpp $(HEX)/board.cpp

SRCS += perf_test.cpp interface.cpp

OBJS := $(patsubst %.cpp, %.o, $(SRCS))
DEPS=$(SRCS:.cpp=.d)


# Top level
all: $(OBJS) libggplib_cpp.so test_hex.bin

libggplib_cpp.so: $(OBJS)
	$(CPP) -shared $(LDFLAGS) $(OBJS) $(LIBS) -o $@

%.o : %.cpp
	$(CPP) $(INCLUDE_PATHS) -I. $(CFLAGS) -c -o $@ $<

test_hex.bin:  test_hex.o
	$(CPP) $(LDFLAGS) $(LIBS) $(OBJS) test_hex.o -o $@

# Cleans
clean :
	$(RM) libggplib_cpp.so $(OBJS) $(DEPS)

-include $(DEPS)
.PHONY: all clean


