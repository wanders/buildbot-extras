import continuous

from buildbot.steps.shell import ShellCommand
from buildbot.steps.shell import SetProperty


def factory(f):
    f.addStep(ShellCommand(command="sleep 10"))

def conf(c):
    c['schedulers'] = []
    c['schedulers'].append(continuous.ContinuousScheduler(name="all",
                                                          builderNames=["test"],
                                                          properties={}))

