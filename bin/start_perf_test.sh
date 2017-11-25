# pipes output to /dev/null, comment out to see what is going on
#

cd $GGPLIB_PATH/src/ggplib
. $GGPLIB_PATH/bin/setup.sh

python scripts/perf_test.py $1 $2 $3
