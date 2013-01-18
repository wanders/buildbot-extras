import syslogstatus


def conf(c):
    n = syslogstatus.SyslogNotifier(host="127.0.0.1", port=514, mode="change", interesting_properties=['-foo', 'halfbuildnum', '-buildnummod5'])
    c['status'].append(n)
