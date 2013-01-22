
from prettyupload import PrettyUpload


def conf(c):
    pass

def factory(f):
    f.addStep(PrettyUpload('/etc/motd',
                           masterdest='public_html/motd.txt'))

    f.addStep(PrettyUpload('/usr/share/pixmaps/debian-logo.png',
                           masterdest='public_html/logo.png'))

    f.addStep(PrettyUpload('/etc/motd',
                           masterdest='motd.txt'))
