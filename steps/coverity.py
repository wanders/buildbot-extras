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

import os
import re

from buildbot.steps.shell import ShellCommand


class _CoverityAnalyze(ShellCommand):
    def describe(self, done=False):
        if done:
            return ["Coverity", "analyse"]
        return ["Coverity", "analysing"]


def CoverityAnalyze(coverityPath, reportDir, disable=None, usermodel=None):
    command = [os.path.join(coverityPath, "cov-analyze"),
               "--dir", reportDir,
               "--all", "--enable-constraint-fpp", "--enable-callgraph-metrics"]
    if disable is not None:
        command.extend(["--disable", disable])
    if usermodel is not None:
        command.extend(["--user-model-file", usermodel])

    return _CoverityAnalyze(command=command)


class _CoverityReport(ShellCommand):
    def describe(self, done=False):
        if done:
            return ["Coverity", "reporting"]
        return ["Coverity", "report"]

    def createSummary(self, log):
        ShellCommand.createSummary(self, log)
        errors = []
        currerror = None
        for l in log.readlines():
            if l.startswith("Error: "):
                currerror = [l]
                errors.append(currerror)
            elif currerror is not None:
                currerror.append("    " + l)
        if errors:
            self.addCompleteLog('errors', "".join(map("".join, errors)))

        old_count = self.getProperty("coverity-errors", 0)
        self.setProperty("coverity-errors", old_count + len(errors), "CoverityReport")


def CoverityReport(coverityPath, reportDir):
    command = [os.path.join(coverityPath, "cov-format-errors"),
               "--dir", reportDir,
               "--emacs-style"]
    return _CoverityReport(command=command)


class _CoverityCommit(ShellCommand):
    def describe(self, done=False):
        if done:
            return ["Coverity", "committing"]
        return ["Coverity", "comitted"]

    def createSummary(self, log):
        ShellCommand.createSummary(self, log)
        for l in log.readlines():
            m = re.match(r"^New snapshot ID ([0-9]*) added\.", l)
            if m is not None:
                self.setProperty("coverity-snapshot-id", m.group(1), "CoverityCommit")
                break


def CoverityCommit(coverityPath, reportDir, stream, baseDir, locks=None):
    command = [os.path.join(coverityPath, "cov-commit-defects"),
               "--dir", reportDir,
               "--stream", stream,
               "--strip-path", baseDir]
    if locks:
        return _CoverityCommit(command=command, locks=locks)
    else:
        return _CoverityCommit(command=command)
