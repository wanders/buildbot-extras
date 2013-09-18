
from prettyupload import PrettyUpload
from buildbot.process.properties import WithProperties

def conf(c):
    pass

def factory(f):
    f.addStep(PrettyUpload('/etc/motd',
                           masterdest='public_html/motd.txt'))

    f.addStep(PrettyUpload('/usr/share/pixmaps/debian-logo.png',
                           masterdest=WithProperties('public_html/logo-%(buildnumber)s.png')))

    f.addStep(PrettyUpload('/etc/motd',
                           masterdest='motd.txt'))
