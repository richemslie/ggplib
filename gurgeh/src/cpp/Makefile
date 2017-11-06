
INCLUDE_PATH = $(GGPLIB_PATH)/src/cpp
LIB_PATH = $(GGPLIB_PATH)/src/cpp

AR = ar
RM = rm -f
CPP = g++

CFLAGS = -MMD -MP -g -Wall -Werror -Woverloaded-virtual -Wnon-virtual-dtor -O3 -fPIC -fomit-frame-pointer -std=c++11
LDFLAGS = -g -MMD -MP -Wall -Werror -Woverloaded-virtual -Wnon-virtual-dtor -O3 -fomit-frame-pointer -std=c++11


SRCS = mcts.cpp worker.cpp
SRCS += interface.cpp

CORE_OBJS = $(patsubst %.cpp, %.o, $(SRCS))
OBJS := $(CORE_OBJS)
DEPS=$(SRCS:.cpp=.d)

# Top level
all: $(OBJS) libgurgehplayerlib_cpp.so

fresh : clean all

# Compiles
libgurgehplayerlib_cpp.so: $(OBJS)
	$(CPP) -shared $(CORE_OBJS) $(LDFLAGS) -L $(LIB_PATH) -pthread -lrt -lggplib_cpp -o libgurgehplayerlib_cpp.so

%.o : %.cpp
	$(CPP) -I $(INCLUDE_PATH) $(CFLAGS) -c -o $@ $<

# Cleans
clean :
	$(RM) $(OBJS) $(DEPS)

realclean : clean
	$(RM) *.so *.log core*

-include $(DEPS)
.PHONY: all fresh clean realclean


