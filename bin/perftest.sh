P=$GGPLIB_PATH

$P/bin/start_perf_test.sh $P/rulesheets/ticTacToe.kif
sleep 2
$P/bin/start_perf_test.sh $P/rulesheets/connectFour.kif
sleep 2
$P/bin/start_perf_test.sh $P/rulesheets/breakthrough.kif
sleep 2
$P/bin/start_perf_test.sh $P/rulesheets/speedChess.kif
sleep 2
$P/bin/start_perf_test.sh $P/rulesheets/reversi.kif
sleep 2
$P/bin/start_perf_test.sh $P/rulesheets/hex.kif
sleep 2

