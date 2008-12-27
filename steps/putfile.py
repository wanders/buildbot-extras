#
# This is mostly just the same as FileDownload, just that contents are
# specified directly in the buildstep. With properties expanded. For
# the slave it looks like a normal FileDownload, so slaves doesn't
# need to be updated.
#
# Example:
# 
#  f.addStep(PutFile(data=WithProperties('#define VERSION "autobuild-%(buildnumber)s"\n'),
#                    slavedest='localconfig.h'))
#
# data can be a list:
#
# d = [WithProperties('#define BUILDNUM %(buildnumber)s\n'),
#      WithProperties('#define SLAVENAME "%(slavename)s"\n'),
#      WithProperties('#define INCLUDETESTS %(tests)s\n')]
# f.addStep(PutFile(data=d, slavedest='localconfig.h'))
#
# Written (copied from transfer.py) by Anders Waldenborg <anders@0x63.nu>
#

import os
from twisted.spread import pb
from twisted.python import log
from buildbot.process.buildstep import BuildStep
from buildbot.process.buildstep import SUCCESS, FAILURE
from buildbot.interfaces import BuildSlaveTooOldError

from buildbot.steps.transfer import StatusRemoteCommand

from StringIO import StringIO

class _StringReader(pb.Referenceable):
    """
    Helper class that acts as a file-object with read access
    """

    def __init__(self, data):
        self.fp = StringIO(data)

    def _remote_read(self, maxlength):
        """
        Called from remote slave
        """
        return self.fp.read(maxlength)

    def remote_close(self):
        pass


class PutFile(BuildStep):
    """
    Create a file on buildslave with the specified contents.

    Arguments::

     ['data']      List of data (properties are expanded)
     ['slavedest'] filename of destination file at slave
     ['workdir']   string with slave working directory relative to builder
                   base dir, default 'build'
     ['blocksize'] maximum size of each block being transfered
     ['mode']      use this to set the access permissions of the resulting
                   buildslave-side file. This is traditionally an octal
                   integer, like 0644 to be world-readable (but not
                   world-writable), or 0600 to only be readable by
                   the buildslave account, or 0755 to be world-executable.
                   The default (=None) is to leave it up to the umask of
                   the buildslave process.

    """

    name = 'putfile'

    def __init__(self, data, slavedest,
                 workdir="build", blocksize=16*1024, mode=None,
                 **buildstep_kwargs):
        BuildStep.__init__(self, **buildstep_kwargs)
        self.addFactoryArguments(data=data,
                                 slavedest=slavedest,
                                 workdir=workdir,
                                 blocksize=blocksize,
                                 mode=mode,
                                 )

        self.data = data
        self.slavedest = slavedest
        self.workdir = workdir
        self.blocksize = blocksize
        assert isinstance(mode, (int, type(None)))
        self.mode = mode

    def start(self):
        properties = self.build.getProperties()

        version = self.slaveVersion("downloadFile")
        if not version:
            m = "slave is too old, does not know about downloadFile"
            raise BuildSlaveTooOldError(m)

        data = "".join(properties.render(self.data))
        slavedest = properties.render(self.slavedest)
        log.msg("PutFile started, to slave %r" % slavedest)

        self.step_status.setColor('yellow')
        self.step_status.setText(['downloading', "to",
                                  os.path.basename(slavedest)])

        # setup structures for reading the file
        reader = _StringReader(data)

        # default arguments
        args = {
            'slavedest': slavedest,
            'maxsize': None,
            'reader': reader,
            'blocksize': self.blocksize,
            'workdir': self.workdir,
            'mode': self.mode,
            }

        self.cmd = StatusRemoteCommand('downloadFile', args)
        d = self.runCommand(self.cmd)
        d.addCallback(self.finished).addErrback(self.failed)

    def finished(self, result):
        if self.cmd.stderr != '':
            self.addCompleteLog('stderr', self.cmd.stderr)

        if self.cmd.rc is None or self.cmd.rc == 0:
            self.step_status.setColor('green')
            return BuildStep.finished(self, SUCCESS)
        self.step_status.setColor('red')
        return BuildStep.finished(self, FAILURE)


