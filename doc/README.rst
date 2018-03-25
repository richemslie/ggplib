======
GGPLib
======

Welcome to GGPLib!  GGPLib is a python/c++ library that takes some of the work out of writing a
player in General Game Playing.  It is largely inspired off the java ggp-base framework.  It is a
fairly minimal framework in comparison, and the emphasis on being able to write a competitive (as
of 2016 at least) players without getting bogged down in the details of writing a fast state
machine.

Major feature is a fully optimized propnet statemachine and the ability to write players in both
python and c++.  Players included are :

1. python legal/random players
2. python monte carlo player
3. c++ random/legal player
4. a very simple/minimal MCTS player
5. ggtest - a test player for Tiltyard (just a configuration and some randomness to 4)


propnet statemachine
====================

The propnet statemachine is very fast.  The interface is designed to be used without memory
allocation and with the same interface between c++/python code.  Full documentation will come soon!

The propnet itself was written by Alex Landau and is found in ggp-base.  Most (if not all) of the
heavy lifting was already done and most of the credit goes to Alex and Sam Schreiber for their work
in ggp-base.


build / running instructions
============================

1. To simplify installing, lets start with a fresh Ubuntu install (17.10).  Most of the packages can
   be skipped/replaced depending on your install, etc.

2. Log in with your user.  Install basic build tools: java, mercurial, git, pypy, gcc and make.

.. code-block:: shell

    sudo apt install git
    sudo apt install java-common default-jre default-jdk
    sudo apt install pypy pypy-dev virtualenv g++ make libjsoncpp-dev

3. Go to whenever you want to place the code

.. code-block:: shell

    # Clone repo wherever
    git clone https://github.com/ggplib/k273
    cd k273
    . bin/setup.sh
    cd src/cpp
    make install
    cd ../../..

    # Clone repo wherever
    git clone https://github.com/ggplib/ggplib
    cd ggplib

    # Setup pypy / install twisted
    virtualenv -p pypy bin/install/_pypy
    . ./bin/install/_pypy/bin/activate
    pip install twisted

    # get ggp-base, and compile java bytecode
    git clone https://github.com/ggp-org/ggp-base
    ln -s `pwd`/src/java/propnet_convert `pwd`/ggp-base/src/main/java
    cd ggp-base
    ./gradlew classes assemble

    # set up environment
    cd ../
    . bin/setup.sh

    # Build the c++ code.  everything should build without warnings.
    cd src/cpp
    make

4.  To test things are working.  Will test ggp-base connection, build propnet state machine.  Test
    the c++ interface.  And performance test a bunch of games.

.. code-block:: shell

    cd $GGPLIB_PATH
    perftest.sh

5.  Config options for ggtest player are found at $GGPLIB_PATH/src/ggplib/player/proxy.py

    To run on ggtest1 on port 9147:

.. code-block:: shell

    cd $GGPLIB_PATH
    ggtest1.sh 9147

6.  (Optional)
    Gurgeh presents a full player utilising GGPLib.
    To build gurgeh, clone and make.
    Config options for Gurgeh player are found at gurgeh/src/gurgeh/player.py
    To build and run:

.. code-block:: shell

    # Clone repo wherever
    git clone https://github.com/ggplib/gurgeh
    cd gurgeh
    . bin/setup.sh
    cd src/cpp
    make
    cd ../gurgeh

    # run Gurgeh on port 9147
    python player.py 9147

7.  (Optional) To run tests.

.. code-block:: shell

    cd $GGPLIB_PATH
    . bin/setup.sh
    pip install pytest
    cd src/ggplib
    py.test -s

8.  (Optional) To use database lookup.  Make a big pot of coffee - it will take a while.

.. code-block:: shell

    cd $GGPLIB_PATH
    . bin/setup.sh

    # cleanup any old files
    git clean -f -d -x data

    git clone https://github.com/ggp-org/ggp-repository.git
    cd ggp-repository/war/root/games/
    find . -name *.kif | xargs python $GGPLIB_PATH/src/ggplib/scripts/create_rulesheets.py -p

    cd $GGPLIB_PATH
    rm -rf ggp-repository

9.  (Optional) Docs.

.. code-block:: shell

    cd $GGPLIB_PATH
    . bin/setup.sh

    pip install sphinx
    cd doc
    make html




Other stuff
===========
* todo
