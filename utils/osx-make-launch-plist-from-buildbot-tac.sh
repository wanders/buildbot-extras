#/bin/bash

set -e

# grab config from buildbot.tac, somewhat hackish and unsafe
eval $(sed -n '/^\([a-z]*\) = [^(]*$/{s/ = /=/;p;}' buildbot.tac)

label="net.sourceforge.buildbot.slave.$slavename.plist"

echo "Creating $label"
echo " copy it to /Library/LaunchDaemons"
echo " ensure it is owned by root:wheel"
echo
echo " i.e execute this:"
echo " # sudo mv $label /Library/LaunchDaemons/"
echo " # sudo chown root:wheel /Library/LaunchDaemons/$label"
echo " # sudo launchctl load /Library/LaunchDaemons/$label"
echo  

tidy -xml -q -i -w 1000 >"$label" <<__EOF__
<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN" "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0">
<dict>
	<key>StandardOutPath</key><string>twistd.log</string>
	<key>StandardErrorPath</key><string>twistd-err.log</string>
	<key>EnvironmentVariables</key><dict><key>PATH</key><string>$PATH</string></dict>
	<key>KeepAlive</key><dict><key>SuccessfulExit</key><false/></dict>
	<key>Label</key><string>net.sourceforge.buildbot.slave.$slavename</string>
	<key>ProgramArguments</key><array><string>$(which twistd)</string><string>-no</string><string>-y</string><string>./buildbot.tac</string></array>
	<key>RunAtLoad</key><true/>
	<key>UserName</key><string>$(whoami)</string>
	<key>GroupName</key><string>daemon</string>
	<key>WorkingDirectory</key><string>$(pwd)</string>
</dict>
</plist>
__EOF__
