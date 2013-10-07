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

from buildbot.steps.shell import Compile


class PartialWarningsCompile(Compile):
    partialwarningStart = None
    partialwarningEnd = None
    partialwarningProperty = None

    def __init__(self, partialwarningStart=None, partialwarningEnd=None, partialwarningProperty=None, **kwargs):
        Compile.__init__(self, **kwargs)
        self.partialwarningStart = partialwarningStart
        self.partialwarningEnd = partialwarningEnd
        self.partialwarningProperty = partialwarningProperty
        self.addFactoryArguments(partialwarningStart=self.partialwarningStart)
        self.addFactoryArguments(partialwarningEnd=self.partialwarningEnd)
        self.addFactoryArguments(partialwarningProperty=self.partialwarningProperty)

    def createSummary(self, log):
        Compile.createSummary(self, log)

        if not self.warningPattern:
            return

        wre = self.warningPattern
        if isinstance(wre, str):
            import re
            wre = re.compile(wre)

        interested = True
        if self.partialwarningStart:
            interested = False
        warnings = []
        for line in log.getText().split("\n"):
            if line == self.partialwarningStart:
                interested = True
            if line == self.partialwarningEnd:
                interested = False
            if interested and wre.match(line):
                warnings.append(line)

        if warnings:
            self.addCompleteLog("partialwarnings", "\n".join(warnings) + "\n")

        if self.partialwarningProperty is not None:
            old_count = self.getProperty(self.partialwarningProperty, 0)
            self.setProperty(self.partialwarningProperty, old_count + len(warnings), "PartialWarningsCompile")
        else:
            old_count = self.getProperty("partial-warnings-count", 0)
            self.setProperty("partial-warnings-count", old_count + len(warnings), "PartialWarningsCompile")
