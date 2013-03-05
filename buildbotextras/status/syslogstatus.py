# Copyright (C) 2008-2013 Anders Waldenborg et al.
#
# Permission is hereby granted, free of charge, to any person obtaining
# a copy of this software and associated documentation files (the
# "Software"), to deal in the Software without restriction, including
# without limitation the rights to use, copy, modify, merge, publish,
# distribute, sublicense, and/or sell copies of the Software, and to
# permit persons to whom the Software is furnished to do so, subject to
# the following conditions:
#
# The above copyright notice and this permission notice shall be
# included in all copies or substantial portions of the Software.
#
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND,
# EXPRESS OR IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF
# MERCHANTABILITY, FITNESS FOR A PARTICULAR PURPOSE AND
# NONINFRINGEMENT. IN NO EVENT SHALL THE AUTHORS OR COPYRIGHT HOLDERS BE
# LIABLE FOR ANY CLAIM, DAMAGES OR OTHER LIABILITY, WHETHER IN AN ACTION
# OF CONTRACT, TORT OR OTHERWISE, ARISING FROM, OUT OF OR IN CONNECTION
# WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE SOFTWARE.

from buildbot.status import base
import socket
from buildbot.status.builder import FAILURE, SUCCESS, WARNINGS, Results
from time import strftime


def messagify(prop):
    (prop, oldval, newval, _) = prop
    return "%s: %s->%s" % (prop, oldval, newval)


def get_previous_with_same(build, prop):
    prev = build.getPreviousBuild()
    if prop is None:
        return prev

    try:
        propval = build.getProperty(prop)
    except:
        propval = None

    while prev:
        try:
            if prev.getProperty(prop) == propval:
                return prev
        except:
            if propval is None:
                return prev
        prev = prev.getPreviousBuild()
    return None


class SyslogNotifier(base.StatusReceiverMultiService):

    def __init__(self, host="127.0.0.1", port=514, mode="all", interesting_properties=[], same_property=None, buildid_property="branch"):
        base.StatusReceiverMultiService.__init__(self)
        self.watched = []
        self.status = None
        self.sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self.sysloghost = host
        self.syslogport = port
        self.mode = mode
        self.interesting_properties = interesting_properties
        self.same_property = same_property
        self.buildid_property = buildid_property

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
        return self  # subscribe to this builder

    def buildFinished(self, name, build, results):
        # here is where we actually do something.
        changed = False
        proplist = []
        prev = get_previous_with_same(build, self.same_property)

        if prev is not None:
            prevresults = prev.getResults()
        else:
            prevresults = results

        last_nonfailing = prev
        while last_nonfailing and last_nonfailing.getResults() == FAILURE:
            last_nonfailing = get_previous_with_same(last_nonfailing, self.same_property)

        if prev:
            if prev.getResults() != results:
                changed = True
        else:
            # Always log initial pushes that causes failures
            if results != SUCCESS:
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

        goodprops = [x for x in proplist if x[3] is True]
        badprops = [x for x in proplist if x[3] is False]
        otherprops = [x for x in proplist if x[3] is None]

        blamelist = ",".join(build.getResponsibleUsers())

        goodwork = True

        try:
            buildid = "#" + str(build.getProperty(self.buildid_property))
        except KeyError:
            buildid = ""

        msg = "Build %s%s completed: " % (name, buildid)
        msg += Results[results].upper()
        if results == WARNINGS:
            goodwork = (prevresults != SUCCESS)
        elif results == FAILURE:
            goodwork = False

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

        if otherprops:
            msg += " (also changed: %s)" % (", ".join(map(messagify, otherprops)))

        hdr = "<1>" + strftime("%b %e %H:%M:%S") + " " + socket.gethostname() + " buildbot: "

        self.sock.sendto(hdr + msg, (self.sysloghost, self.syslogport))
