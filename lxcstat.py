#!/usr/bin/env python3
# -*- coding: utf-8 -*-
#
#  lxcstat.py
#  
#  Copyright 2015 Nikonov Alexander <sgloom@gmail.com>
#  
#  This program is free software; you can redistribute it and/or modify
#  it under the terms of the GNU General Public License as published by
#  the Free Software Foundation; either version 2 of the License, or
#  (at your option) any later version.
#  
#  This program is distributed in the hope that it will be useful,
#  but WITHOUT ANY WARRANTY; without even the implied warranty of
#  MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#  GNU General Public License for more details.
#  
#  You should have received a copy of the GNU General Public License
#  along with this program; if not, write to the Free Software
#  Foundation, Inc., 51 Franklin Street, Fifth Floor, Boston,
#  MA 02110-1301, USA.
#  
#  

import ast, sys, time, re
from optparse import OptionParser
from collections import Iterable
from subprocess import Popen, PIPE


interval = 1

def main():
		
	parser = OptionParser()
	parser.add_option("-t", "--type", dest="param_type", choices=['mem','memtotal','memused','cpu'],\
	 help="show info about memory (mem) or cpu usage (cpu). Show only total memory (memtotal) or used memory (memused) in megabytes.")
	parser.add_option("-n", "--name", dest="container_name", help="NAME for name of the container", metavar = "NAME")
	(options, args) = parser.parse_args()
	
	if not options.container_name:
		parser.error('Container name not given')
	global cgroup_dir
	cgroup_dir = '/sys/fs/cgroup/lxc/%s/' % options.container_name
	proc = Popen(["lxc-info", "-q", "-s", "-n", options.container_name],
	stdout = PIPE, stderr = PIPE)
	output , err = proc.communicate()
	output = str(output)
	
	if not re.search('(RUNNING|running)', output):
		sys.stderr.write("LXC container \'" + options.container_name + "\' is not running or doesn't exist.\n")
		sys.exit(1)
	
	if options.param_type == 'mem':
		print('Memory used:',str(get_mem()['memory_used'])+'M')
		print('Memory total:',str(get_mem()['memory_total'])+'M')
	elif options.param_type == 'cpu':
		print('Cpu Usage %:',cpu_usage())
	elif options.param_type == 'memtotal':
		print(get_mem()['memory_total'])
	elif options.param_type == 'memused':
		print(get_mem()['memory_used'])
	else:
		print('Cpu Usage %:',cpu_usage())
		print('Memory used:',str(get_mem()['memory_used'])+'M')
		print('Memory total:',str(get_mem()['memory_total'])+'M')
	
	return 0
	
def get_cpu():
	values = {}
	try:
		with open('%s/cpuacct.usage' % cgroup_dir,"r") as cpuacctusage_file:
			values['cpu_usage'] = int(cpuacctusage_file.read())
	except IOError:
		sys.stderr.write("Can't open cpuacct.usage\n")
		sys.exit(1)
	return values
	
def get_mem():
	values = {}
	try:
		with open('%s/memory.limit_in_bytes' % cgroup_dir,"r") as memlimit_file:
			values['memory_total'] = int(int(memlimit_file.read()) / 1048576)
	except IOError:
		sys.stderr.write("Can't open memory.limit_in_bytes\n")
		sys.exit(1)
	try:
		with open('%s/memory.usage_in_bytes' % cgroup_dir,"r") as memusage_file:
			values['memory_used'] = int(int(memusage_file.read()) / 1048576)
	except IOError:
		sys.stderr.write("Can't open memory.usage_in_bytes\n")
		sys.exit(1)
	return values
	
def cpu_usage():
	try:
		with open('%s/cpuset.cpus' % cgroup_dir,"r") as cpusetfile:
			cpulist = ast.literal_eval(cpusetfile.read())
	except IOError:
		sys.stderr.write("Can't open cpuset.cpus\n")
		sys.exit(1)
	cpus = 0
	if not isinstance(cpulist, Iterable):
		cpulist = [cpulist]

	for n in cpulist:
		if n < 0:
			cpus += (abs(n) + 1)
		else:
			cpus += 1
	firstvalues = get_cpu()
	time.sleep(interval)
	secondvalues = get_cpu()
	deltacpu = secondvalues['cpu_usage'] - firstvalues['cpu_usage']
	usedcpu_ns = float(deltacpu / interval)
	used_s = usedcpu_ns / 1000000000
	percent_cpu = int((used_s / cpus) * 100)
	return '{:.1f}'.format(percent_cpu)
	
def printhelp():
	print("""Usage:\nlxcinfo.py [options] -n NAME\n
	Options:
	-t [mem|memtotal|memeused|cpu]	show info about memory or cpu usage.
	memtotal and memused show only total or used memory size in units of megabytes.
	-n NAME		NAME for name of the container""")

if __name__ == '__main__':
	main()
