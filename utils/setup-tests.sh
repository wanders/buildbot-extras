set -e


srcdir=$(cd ..; pwd)

export PYTHONPATH=$srcdir/status:$srcdir/utils/tests/syslogstatus

basedir=$(mktemp --tmpdir -d bbtests.XXXXXXXXXXX)

echo Using $basedir

buildbot create-master $basedir/master
buildbot create-slave $basedir/slave 127.0.0.1:9989 test test


cp simple-master.cfg $basedir/master/master.cfg


(cd $basedir/master; twistd -n -y buildbot.tac) &
(cd $basedir/slave; twistd -n -y buildbot.tac) &

sleep 2

tail -f $basedir/master/twistd.log $basedir/slave/twistd.log &


for x in {1..20}; do
    #buildbot sendchange --master=127.0.0.1:9989 -utest file.foo
    sleep 2
done



#kill $(cat $basedir/slave/twistd.pid) $(cat $basedir/master/twistd.pid)

wait
