#!/usr/bin/python
import os

# -- my version of buildbot.slave.commands.Git -- #
from buildbot.slave.commands import SourceBase, ShellCommand, rmdirRecursive
from buildbot.slave.registry import registerSlaveCommand

class BitKeeperSlave(SourceBase):
    """BitKeeper specific VC operation. In addition to the arguments
    handled by SourceBase, this command reads the following keys:

    ['repourl'] (required): the BitKeeper repository string
    """

    header = "bitkeeper operation"

    def setup(self, args):
        SourceBase.setup(self, args)
        self.repourl = args['repourl']
        self.sourcedata = "%s" % (self.repourl)
    
    def _fullSrcdir(self):
        return os.path.join(self.builder.basedir, self.srcdir)
    
    def sourcedirIsUpdateable(self):
        # FIXME what the hell is this supposed to do?
        if os.path.exists(os.path.join(self._fullSrcdir(),
                                       ".buildbot-patched")):
            return False
        return os.path.isdir(os.path.join(self._fullSrcdir(), "BitKeeper"))
    
    def doVCUpdate(self):
        command = ['bk', '-q', 'pull']
        self.sendStatus({"header": "updating from %s\n"
            % (self.repourl)})
        c = ShellCommand(self.builder, command, self._fullSrcdir(),
            sendRC=False, timeout=self.timeout)
        self.command = c
        d = c.start()
        d.addCallback(self._abandonOnFailure)
        #d.addCallback(self._didFetch)
        return d

    def doVCFull(self):
        # Clone the repository into a temporary dir
        # FIXME the temporary dir will not be subject to deletion.
        if self.mode == "export":
            srcdir = self._fullSrcdir()
            tmpdir = os.path.join(self.builder.basedir, 'temp_clone')
            if os.path.exists(tmpdir):
                from shutil import rmtree
                rmtree(tmpdir)
            #rmdirRecursive(tmpdir)
            command = ['bk', 'clone', '-q', self.repourl, tmpdir]
            c = ShellCommand(self.builder, command, tmpdir, sendRC=False,
                timeout=self.timeout)
            self.command = c
            d = c.start()
            def _export(res):
                command = ['bk', 'export', '-Tw', tmpdir,
                    self._fullSrcdir()]
                c = ShellCommand(self.builder, command, tmpdir,
                    sendRC=False, timeout=self.timeout)
                self.command = c
                return c.start()
            d.addCallback(_export)
            return d
        else:
            srcdir = self._fullSrcdir()
            os.mkdir(srcdir)
            command = ['bk', '-q', 'clone', self.repourl, srcdir]
            c = ShellCommand(self.builder, command, srcdir, sendRC=False, timeout=self.timeout)
            self.command = c
            return c.start()

    def parseGotRevision(self):
        if self.mode == "export":
            rev_file = os.path.join(self.builder.basedir, 'temp_clone',
            'ChangeSet')
        else:
            rev_file = os.path.join(self._fullSrcdir(), 'ChangeSet')

        command = ['bk', 'log', '-r+', '-d:MD5KEY:', rev_file]
        c = ShellCommand(self.builder, command, self._fullSrcdir(),
            sendRC=False, keepStdout=True)
        c.usePTY = False
        d = c.start()
        def _parse(res):
            return c.stdout.strip()
        d.addCallback(_parse)
        return d

registerSlaveCommand("bitkeeper", BitKeeperSlave, "2.5")

## -- My version of builbot.step.source.Git --
from buildbot.steps.source import Source, LoggedRemoteCommand
from buildbot.interfaces import BuildSlaveTooOldError

class BitKeeper(Source):
    """Check out a source tree from a bitkeeper repository 'repourl'."""

    name = "bitkeeper"

    def __init__(self, repourl, **kwargs):
        """
        @type  repourl: string
        @param repourl: the URL which points at the bitkeeper repository
        """
        Source.__init__(self, **kwargs)
        self.addFactoryArguments(repourl=repourl)
        self.args.update({'repourl': repourl})

    def computeSourceRevision(self, changes):
        if not changes:
            return None
        return changes[-1].revision

    def startVC(self, branch, revision, patch):
        self.args['branch'] = branch
        self.args['revision'] = revision
        self.args['patch'] = patch
        slavever = self.slaveVersion("bitkeeper")
        if not slavever:
            raise BuildSlaveTooOldError("slave is too old, does not know "
                                        "about bitkeeper")
        cmd = LoggedRemoteCommand("bitkeeper", self.args)
        self.startCommand(cmd)

# vim:set shiftwidth=4 tabstop=4 expandtab textwidth=79:
