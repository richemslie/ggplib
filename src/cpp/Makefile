include $(K273_PATH)/src/cpp/Makefile.in

LIBS = -L $(K273_PATH)/src/cpp/k273 -lk273

CFLAGS += -fPIC

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
#-ljsoncpp

libggplib_cpp.so: $(OBJS)
	$(CPP) -shared $(LDFLAGS) $(CORE_OBJS) $(LIBS) -o $@

%.o : %.cpp
	$(CPP) $(INCLUDE_PATHS) -I. $(CFLAGS) -c -o $@ $<

# Cleans
clean :
	$(RM) $(OBJS) $(DEPS)

realclean : clean
	$(RM) *.so *.log core*

-include $(DEPS)
.PHONY: all fresh clean realclean


