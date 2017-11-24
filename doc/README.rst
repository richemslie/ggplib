======
GGPLib
======

XXX Needs testing/updated... WIP

Welcome to GGPLib!  GGPLib is a python/c++ implementation of a player in General Game
Playing.  It is roughly based off the java ggp-base framework.  It is a fairly minimal framework in
comparison, and the emphasis on being able to write a competitive (as of 2016 at least) players
without getting bogged down in the details of writing a fast state machine.

It initially will include the a fully optimized propnet, and the ability to write players
in both python and c++.  Currently there are 4 players:

1. python random player
2. c++ random player
3. c++ legal player
4. a very simple/minimal MCTS player (too replace 4 above, maybe)
5. python monte carlo player
6. ggtest - a test player for Tiltyard

Hopefully adding soon:

* a prover reusing the same state machine interface
* a GDL game lookup mechanism to store information about games between matches

propnet statemachine
====================

The propnet statemachine is fairly fast and scores very well against other propnets in gdl-perf.  The
interface is designed to be used without memory allocation and with the same interface between
c++/python code.  Full documentation will come soon!

The propnet itself was written by Alex Landau and is found in ggp-base.  Most (if not all) of the
heavy lifting was already done and most of the credit goes to Alex and Sam Schreiber for their work
in ggp-base. And thanks for running Tiltyard website.


build / running instructions
============================

1. To simplify installing, lets start with a fresh Ubuntu install (16.10).  Most of the packages can
   be skipped/replaced depending on your install, etc.

2. Log in with your user.  Install basic build tools: java, mercurial, git, pypy, gcc and make.

.. code-block:: shell

   $ sudo apt install git
   $ sudo apt install java-common default-jre default-jdk
   $ sudo apt install pypy pypy-dev virtualenv g++ make

3. Go to whenever you want to place the code

.. code-block:: shell

   # Clone repo wherever
   $ git clone https://github.com/richemslie/ggplib
   $ cd ggplib

   # Setup pypy / install twisted
   $ virtualenv -p pypy bin/install/_pypy
   $ . ./bin/install/_pypy/bin/activate
   $ pip install twisted

   # get custom ggp-base, and compile java bytecode
   $ git clone https://github.com/richemslie/ggp-base
   $ cd ggp-base
   $ ./gradlew classes assemble

   # set up environment
   $ cd ../
   $ . bin/setup.sh

   # Build the c++ code.  everything should build without warnings.
   $ cd src/cpp
   $ make

   # TODO XXX docs

4.  To test things are working.  Will test ggp-base connection, build propnet state machine.  Test
    the c++ interface.  And performance test a bunch of games.

.. code-block:: shell

    $ cd $GGPLIB_PATH
    $ perftest.sh

5.  Config options for ggtest player are found at $GGPLIB_PATH/src/ggplib/player/proxy.py

    To run on ggtest1 on port 9147:

.. code-block:: shell

    $ cd $GGPLIB_PATH
    $ ggtest1.sh 9147

6.  (Optional) To build run Gurgeh.  Gurgeh presents a full player utilising GGPLib.  This could be
    in separate repo - it is presented here as an example of a standalone player.  All the code is
    under $GGPLIB_PATH/gurgeh/src.
    Config options for Gurgeh player are found at $GGPLIB_PATH/gurgeh/src/gurgeh/gurgeh.py.
    To build and run:

.. code-block:: shell

    $ cd $GGPLIB_PATH/gurgeh/src/cpp
    $ make

    # run Gurgeh on port 9147
    $ cd $GGPLIB_PATH/gurgeh/src/gurgeh
    $ python gurgeh.py 9147


Other stuff
===========

* todo
* more todo
