from distutils.core import setup

setup(
    name='buildbot-extras',
    version='2',
    url='https://github.com/wanders/buildbot-extras',
    author='Anders Waldenborg',
    author_email='anders@0x63.nu',
    packages=['buildbotextras', 'buildbotextras.status', 'buildbotextras.steps'],
)
