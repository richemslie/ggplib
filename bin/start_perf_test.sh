# pipes output to /dev/null, comment out to see what is going on
. $GGPLIB_PATH/bin/setup.sh 2>&1 > /dev/null

cd $GGPLIB_PATH/src/ggplib

python scripts/perf_test.py $1 $2 $3
