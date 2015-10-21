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

from buildbot.steps.transfer import FileUpload
from buildbot.status.builder import SUCCESS

IMAGE_FORMATS = ('png', 'jpg', 'svg')
PUB_PREFIX = "public_html/"


class PrettyUpload(FileUpload):
    name = 'prettyupload'

    def finished(self, result):
        if result == SUCCESS:
            mdest = self.masterdest
            ext = mdest[-3:]
            bname = mdest.split("/")[-1]

            if mdest.startswith(PUB_PREFIX):
                reldest = mdest[len(PUB_PREFIX):]
                if ext in IMAGE_FORMATS:
                    l = ['<a href="/%s"><img src="/%s"></a>' % (reldest, reldest)]
                else:
                    l = []
                    self.addURL(bname, "/" + reldest)
            else:
                l = [bname]
            self.step_status.setText(['Uploaded'] + l)
        return FileUpload.finished(self, result)
