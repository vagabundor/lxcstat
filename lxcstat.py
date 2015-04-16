#!/usr/bin/env python3
# -*- coding: utf-8 -*-
#
# lxcstat.py
#  
#  Copyright 2015 Nikonov Alexander <sgloom@gmail.com>
#


import sys
import time
import re
from optparse import OptionParser
from subprocess import Popen, PIPE


interval = 1


def main():
    parser = OptionParser()
    parser.add_option("-t", "--type", dest="param_type",
                      choices=['mem', 'memtotal', 'memused', 'cpu'],
                      help="Show info about memory (mem) or cpu usage (cpu)."
                           "Only total memory (memtotal) or used memory (memused) in megabytes.")
    parser.add_option("-n", "--name", dest="container_name", help="NAME for name of the container", metavar="NAME")
    (options, args) = parser.parse_args()

    if not options.container_name:
        parser.error('Container name not given')
    global cgroup_dir
    cgroup_dir = '/sys/fs/cgroup/lxc/%s/' % options.container_name
    proc = Popen(["lxc-info", "-q", "-s", "-n", options.container_name],
                 stdout=PIPE, stderr=PIPE)
    output, err = proc.communicate()
    output = str(output)

    if not re.search('(RUNNING|running)', output):
        sys.stderr.write("LXC container \'" + options.container_name + "\' is not running or doesn't exist.\n")
        sys.exit(1)

    if options.param_type == 'mem':
        print('Memory used:', str(get_mem()['memory_used']) + 'M')
        print('Memory total:', str(get_mem()['memory_total']) + 'M')
    elif options.param_type == 'cpu':
        print('Cpu Usage %:', cpu_usage())
    elif options.param_type == 'memtotal':
        print(get_mem()['memory_total'])
    elif options.param_type == 'memused':
        print(get_mem()['memory_used'])
    else:
        print('Cpu Usage %:', cpu_usage())
        print('Memory used:', str(get_mem()['memory_used']) + 'M')
        print('Memory total:', str(get_mem()['memory_total']) + 'M')

    return 0


def get_cpu():
    values = {}
    try:
        with open('%s/cpuacct.usage' % cgroup_dir, "r") as cpuacctusage_file:
            values['cpu_usage'] = int(cpuacctusage_file.read())
    except IOError:
        sys.stderr.write("Can't open cpuacct.usage\n")
        sys.exit(1)
    return values


def get_mem():
    values = {}
    try:
        with open('%s/memory.limit_in_bytes' % cgroup_dir, "r") as memlimit_file:
            values['memory_total'] = int(int(memlimit_file.read()) / 1048576)
    except IOError:
        sys.stderr.write("Can't open memory.limit_in_bytes\n")
        sys.exit(1)
    try:
        with open('%s/memory.usage_in_bytes' % cgroup_dir, "r") as memusage_file:
            values['memory_used'] = int(int(memusage_file.read()) / 1048576)
    except IOError:
        sys.stderr.write("Can't open memory.usage_in_bytes\n")
        sys.exit(1)
    return values


def cpu_usage():
    try:
        with open('%s/cpuset.cpus' % cgroup_dir, "r") as cpusetfile:
            cpulist = cpusetfile.read().split(',')
            for n_cpulist in range(len(cpulist)):
                if re.search('\d*-\d*', cpulist[n_cpulist]) is not None:
                    cpu_underlist = cpulist[n_cpulist].split('-')
                    cpu_underlist = range(int(cpu_underlist[0]), int(cpu_underlist[1])+1)
                    cpulist += cpu_underlist
                    cpulist.pop(n_cpulist)

    except IOError:
        sys.stderr.write("Can't open cpuset.cpus\n")
        sys.exit(1)

    cpus = len(cpulist)
    firstvalues = get_cpu()
    time.sleep(interval)
    secondvalues = get_cpu()
    deltacpu = secondvalues['cpu_usage'] - firstvalues['cpu_usage']
    usedcpu_ns = float(deltacpu / interval)
    used_s = usedcpu_ns / 1000000000
    percent_cpu = int((used_s / cpus) * 100)
    return '{:.1f}'.format(percent_cpu)


if __name__ == '__main__':
    main()
