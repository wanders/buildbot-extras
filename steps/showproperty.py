# A really trivial build step. Same as ShowProperty but shows the
# property value.
#
# Written by Anders Waldenborg <anders@0x63.nu>

from buildbot.steps.shell import SetProperty

class ShowProperty(SetProperty):
    def getText(self, cmd, results):
        if self.property_changes:
            return [ "%s: %s" % x for x in self.property_changes.items()]
        else:
            return [ "no change" ]
