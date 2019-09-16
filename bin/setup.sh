if [ -z "$K273_PATH" ]; then
    echo "Please set \$K273_PATH"
    return 1
fi

if [ -z "$GGPLIB_PATH" ]; then
    export GGPLIB_PATH=`python2 -c "import os.path as p; print p.dirname(p.dirname(p.abspath('$BASH_SOURCE')))"`
    echo "Automatically setting $GGPLIB_PATH to " $GGPLIB_PATH
fi

if [ -z "$GGP_BASE_PATH" ]; then
    export GGP_BASE_PATH=$GGPLIB_PATH/ggp-base
    echo "Automatically setting $GGP_BASE_PATH to " $GGP_BASE_PATH
fi

# needed since we still use java and ggp-base to create propnet (for now)
export CLASSPATH=$GGP_BASE_PATH/build/classes/main:$GGP_BASE_PATH/build/resources/main:$GGP_BASE_PATH/lib/Guava/guava-14.0.1.jar:$GGP_BASE_PATH/lib/Jython/jython.jar:$GGP_BASE_PATH/lib/Clojure/clojure.jar:$GGP_BASE_PATH/lib/Batik/batik-1.7.jar:$GGP_BASE_PATH/lib/FlyingSaucer/core-renderer.jar:$GGP_BASE_PATH/lib/javassist/javassist.jar:$GGP_BASE_PATH/lib/reflections/reflections-0.9.9-RC1.jar:$GGP_BASE_PATH/lib/Htmlparser/htmlparser-1.4.jar

export PYTHONPATH=$GGPLIB_PATH/src:$PYTHONPATH
export LD_LIBRARY_PATH=$GGPLIB_PATH/src/cpp:$LD_LIBRARY_PATH
export PATH=$GGPLIB_PATH/bin:$PATH
