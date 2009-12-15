from buildbot.status import base
import socket
from buildbot.status.builder import FAILURE, SUCCESS, WARNINGS
from time import strftime

def messagify(prop):
    (prop, oldval, newval, _) = prop
    return "%s: %s->%s" % (prop, oldval, newval)

class SyslogNotifier(base.StatusReceiverMultiService):

    def __init__(self, host="127.0.0.1", port=514, mode="all", interesting_properties=[]):
        base.StatusReceiverMultiService.__init__(self)
        self.watched = []
        self.status = None
        self.sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self.sysloghost = host
        self.syslogport = port
        self.mode = mode
        self.interesting_properties = interesting_properties

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

        changed = False
        proplist = []
        prev = build.getPreviousBuild()

        if prev is not None:
            prevresults = prev.getResults()
        else:
            prevresults = results
 
        last_nonfailing = prev
        while last_nonfailing and last_nonfailing.getResults() == FAILURE:
            last_nonfailing = last_nonfailing.getPreviousBuild()

        if prev:
            if prev.getResults() != results:
                changed = True

        # Only look at properties on non-failing builds
        if results != FAILURE and last_nonfailing:
            for prop in self.interesting_properties:
                gooddir = 0
                if prop[0] == '-':
                    prop = prop[1:]
                    gooddir = -1
                elif prop[0] == '+':
                    prop = prop[1:]
                    gooddir = 1

                try:
                    new = build.getProperty(prop)
                    old = last_nonfailing.getProperty(prop)
                except KeyError:
                    continue

                if new != old:
                    changed = True

                    if gooddir:
                        try:
                            new = int(new)
                            old = int(old)
                        except:
                            gooddir = 0

                    good = None
                    if gooddir == -1:
                        good = (new < old)
                    elif gooddir == 1:
                        good = (new > old)

                    proplist.append((prop, old, new, good))

        if self.mode == "change" and not changed:
            return


        goodprops = [x for x in proplist if x[3] == True]
        badprops = [x for x in proplist if x[3] == False]
        otherprops = [x for x in proplist if x[3] is None]

        blamelist = ",".join(build.getResponsibleUsers())


        goodwork = True

        msg = "Build %s completed:" % name
        if results == SUCCESS:
            msg += " SUCCESS"
        elif results == WARNINGS:
            goodwork = (prevresults == FAILURE)
            msg += " WARNINGS"
        elif results == FAILURE:
            goodwork = False
            msg += " FAILURE"

        if badprops:
            goodwork = False


        if goodwork:
            if goodprops:
                msg += "+(%s)" % (", ".join(map(messagify, goodprops)))
            msg += ", good work %s" % blamelist
        else:
            if badprops:
                msg += "+(%s)" % (", ".join(map(messagify, badprops)))
            msg += ", did you push bad stuff %s?" % blamelist
            otherprops += goodprops
        print otherprops

        if otherprops:
            msg += " (also changed: %s)" % (", ".join(map(messagify, otherprops)))


        hdr = "<1>"+strftime("%b %e %H:%M:%S")+" "+socket.gethostname()+" buildbot: "
        msg = "Build %s completed: %s" % (name, msg)

        self.sock.sendto(hdr+msg, (self.sysloghost, self.syslogport))
