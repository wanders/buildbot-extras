#!/bin/bash

set -e
set -u

testname=$1

utildir=$(dirname "$0")

cd "$utildir"

srcdir=$(cd ..; pwd)

if [[ ! -d "$srcdir/utils/tests/$testname" ]]; then
	echo "Couldn't find test named '$testname'"
	exit 1
fi

export PYTHONPATH="$srcdir/status:$srcdir/steps:$srcdir/utils/tests/$testname"

basedir=$(mktemp --tmpdir -d bbtests.XXXXXXXXXXX)

echo Using "$basedir"

buildbot create-master "$basedir/master"
buildbot create-slave "$basedir/slave" 127.0.0.1:9989 test test


cp simple-master.cfg "$basedir/master/master.cfg"

(cd "$basedir/master"; twistd -y buildbot.tac)
(cd "$basedir/slave"; twistd -y buildbot.tac)

killbuildbot () {
	kill $(cat "$basedir/slave/twistd.pid") $(cat "$basedir/master/twistd.pid")
	sleep 1
	rm -rfv "$basedir"
}

trap killbuildbot EXIT

sleep 2

tail -f "$basedir/master/twistd.log" "$basedir/slave/twistd.log" &


for x in {1..20}; do
    buildbot sendchange --master=127.0.0.1:9989 -utest file.foo
    sleep 2
done



# wait for ctrl-c of tail..

wait
