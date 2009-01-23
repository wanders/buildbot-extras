from buildbot.status import base
import socket
from buildbot.status.builder import FAILURE, SUCCESS, WARNINGS
from time import strftime


class SyslogNotifier(base.StatusReceiverMultiService):

    def __init__(self, host="127.0.0.1", port=514, mode="all"):
        base.StatusReceiverMultiService.__init__(self)
        self.watched = []
        self.status = None
        self.sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self.sysloghost = host
        self.syslogport = port
        self.mode = mode

    def setServiceParent(self, parent):
        """
        @type  parent: L{buildbot.master.BuildMaster}
        """
        base.StatusReceiverMultiService.setServiceParent(self, parent)
        self.setup()

    def setup(self):
        self.status = self.parent.getStatus()
        self.status.subscribe(self)

    def disownServiceParent(self):
        self.status.unsubscribe(self)
        for w in self.watched:
            w.unsubscribe(self)
        return base.StatusReceiverMultiService.disownServiceParent(self)

    def builderAdded(self, name, builder):
        self.watched.append(builder)
        return self # subscribe to this builder

    def buildFinished(self, name, build, results):
        # here is where we actually do something.
        builder = build.getBuilder()

        if self.mode == "change":
            prev = build.getPreviousBuild()
            if prev and prev.getResults() == results:
                return

        blamelist = ", ".join(build.getResponsibleUsers())
        if results == SUCCESS:
            res = "success, good work %s!" % blamelist 
        elif results == WARNINGS:
            res = "warnings, did you push bad stuff %s?" % blamelist
        else:
            res = "failure, did you push bad stuff %s?" % blamelist

        hdr = "<1>"+strftime("%b %e %H:%M:%S")+" "+socket.gethostname()+" buildbot:"
        msg = "Build %s completed: %s" % (name, res)

        self.sock.sendto(hdr+msg, (self.sysloghost, self.syslogport))
