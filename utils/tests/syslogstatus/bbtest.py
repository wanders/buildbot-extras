import syslogstatus

from buildbot.steps.shell import ShellCommand
from buildbot.steps.shell import SetProperty
from buildbot.process.properties import WithProperties


def factory(f):
    f.addStep(ShellCommand(command="echo foo >testfile"))
    # add a property that increases with one every other build
    f.addStep(SetProperty(command=WithProperties("echo $((%(buildnumber)s / 2))"), property="halfbuildnum"))
    f.addStep(SetProperty(command=WithProperties("echo $((5 - (%(buildnumber)s %% 5)))"), property="buildnummod5"))
    f.addStep(SetProperty(command="echo foo", property="foo"))
    # fail every forth build
    f.addStep(ShellCommand(command=WithProperties("exit $((%(buildnumber)s %% 4 == 0))")))

def conf(c):
    n = syslogstatus.SyslogNotifier(host="127.0.0.1", port=514, mode="change", interesting_properties=['-foo', 'halfbuildnum', '-buildnummod5'])
    c['status'].append(n)
