
from prettyupload import PrettyUpload
from buildbot.process.properties import WithProperties

def conf(c):
    pass

def factory(f):
    f.addStep(PrettyUpload('/thisfile/does/not/exist',
                           masterdest='public_html/eexist.txt',
                           haltOnFailure=False))

    f.addStep(PrettyUpload('/etc/debian_version',
                           masterdest='public_html/debian_version.txt',
                           flunkOnFailure=True))

    f.addStep(PrettyUpload('/usr/share/pixmaps/debian-logo.png',
                           masterdest=WithProperties('public_html/logo-%(buildnumber)s.png')))

    f.addStep(PrettyUpload('/etc/debian_version',
                           masterdest='debian_version.txt'))
