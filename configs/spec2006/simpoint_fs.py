# Copyright (c) 2014, The Microsystem Design Laboratory (MDL)
# Department of Computer Science and Engineering, The Pennsylvania State University
# All rights reserved.
#
# The license below extends only to copyright in the software and shall
# not be construed as granting a license to any other intellectual
# property including but not limited to intellectual property relating
# to a hardware implementation of the functionality of the software
# licensed hereunder.  You may use the software subject to the license
# terms below provided that you ensure that this notice is replicated
# unmodified and in its entirety in all distributions of the software,
# modified or unmodified, in source code or in binary form.
#
# Redistribution and use in source and binary forms, with or without
# modification, are permitted provided that the following conditions are
# met: redistributions of source code must retain the above copyright
# notice, this list of conditions and the following disclaimer;
# redistributions in binary form must reproduce the above copyright
# notice, this list of conditions and the following disclaimer in the
# documentation and/or other materials provided with the distribution;
# neither the name of the copyright holders nor the names of its
# contributors may be used to endorse or promote products derived from
# this software without specific prior written permission.
#
# THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDERS AND CONTRIBUTORS
# "AS IS" AND ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT
# LIMITED TO, THE IMPLIED WARRANTIES OF MERCHANTABILITY AND FITNESS FOR
# A PARTICULAR PURPOSE ARE DISCLAIMED. IN NO EVENT SHALL THE COPYRIGHT
# OWNER OR CONTRIBUTORS BE LIABLE FOR ANY DIRECT, INDIRECT, INCIDENTAL,
# SPECIAL, EXEMPLARY, OR CONSEQUENTIAL DAMAGES (INCLUDING, BUT NOT
# LIMITED TO, PROCUREMENT OF SUBSTITUTE GOODS OR SERVICES; LOSS OF USE,
# DATA, OR PROFITS; OR BUSINESS INTERRUPTION) HOWEVER CAUSED AND ON ANY
# THEORY OF LIABILITY, WHETHER IN CONTRACT, STRICT LIABILITY, OR TORT
# (INCLUDING NEGLIGENCE OR OTHERWISE) ARISING IN ANY WAY OUT OF THE USE
# OF THIS SOFTWARE, EVEN IF ADVISED OF THE POSSIBILITY OF SUCH DAMAGE.
#
# Authors: Matt Poremba

import optparse
import sys
import ConfigParser
import operator

import m5
from m5.defines import buildEnv
from m5.objects import *
from m5.util import addToPath, fatal

addToPath('../common')

#from Nehalem import *
from FSConfig import *
from CpuConfig import *
from SysPaths import *
import Simulation
import MemConfig
from Caches import *
import spec_fs as spec_fs
import pyterm
import os
import errno

def mkdir_p(path):
    try:
        os.makedirs(path)
    except OSError as exc: # Python >2.5
        if exc.errno == errno.EEXIST and os.path.isdir(path):
            pass
        else:
            raise

parser = optparse.OptionParser()

# Cache/CPU config options
parser.add_option("--cfg", action="store", type="string", dest="cfg",
                  help="The system config file to use.")
parser.add_option("--machine-type", action="store", type="choice",
                choices=ArmMachineType.map.keys(), default="RealView_PBX")
parser.add_option("--dtb-filename", action="store", type="string",
              help="Specifies device tree blob file to use with device-tree-"\
              "enabled kernels")
parser.add_option("--bare-metal", action="store_true",
                   help="Provide the raw system without the linux specific bits")
parser.add_option("-n", "--num-cpus", type="int", default=1)

# Run options
parser.add_option("--simpoint-mode", type="choice", choices=["init", "checkpoint", "simulate", "check_affinity", "fastfwd", "batch"],
                  default="init")
parser.add_option("--checkpoint-dir", action="store", type="string",
                  default=None, dest="checkpoint_dir",
                  help="Directory containing simpoint checkpoints")
parser.add_option("--init-checkpoint-dir", action="store", type="string",
                  default=None, dest="init_checkpoint_dir",
                  help="Directory containing checkpoint after system boot")
parser.add_option("--benchmark", action="store", type="string", dest="benchmark",
                  help="Name of benchmarks to run, separated by ':'")
parser.add_option("-I", "--max-insts", type="int", default=0,
                  help="Maximum number of instructions to simulate (simulate mode)")
parser.add_option(      "--private-l2", action="store_true", help="Use one L2 per CPU")

# Memory options
parser.add_option("--nvmain-config", type="string", default="", help="NVMain configuration file to use.")
parser.add_option("--nvmain-warmup", action="store_true", help="Warmup memory level caches in NVMain in atomic mode.")
parser.add_option("--mem-size", action="store", type="string", default="2GB",
                  help="Specify the physical memory size (single memory)")
parser.add_option("--mem-type", type="choice", default="simple_mem",
                  choices=MemConfig.mem_names(),
                  help = "type of memory to use")
parser.add_option("--mem-channels", type="int", default=1, # Not used for NVMain
                  help = "number of memory channels")

# Clock timings
parser.add_option("--sys-clock", action="store", type="string",
                  default='2GHz',
                  help = """Top-level clock for blocks running at system
                  speed""")
parser.add_option("--cpu-clock", action="store", type="string",
                  default='2GHz',
                  help="Clock for blocks running at CPU speed")
parser.add_option("--sys-voltage", action="store", type="string",
                  default='1.0V',
                  help="Top-level voltage for blocks running at system power supply")
# FS Options
parser.add_option("--kernel", action="store", type="string")
parser.add_option("--disk-image", action="store", type="string", default=None,
                  help="Path to the disk image to use.")
parser.add_option("--init-param", action="store", type="int", default=0,
                  help="""Parameter available in simulation with m5
                          initparam""")
parser.add_option("--script", action="store", type="string")
parser.add_option("--isolated-cpus", type="string", help="Comma delimited list of CPUs which should be isolated")

# Add NVMain override options
argnum = 1
for arg in sys.argv:
    if arg[:9] == "--nvmain-" and arg != '--nvmain-config' and arg != '--nvmain-warmup':
        parser.add_option(arg, type="string", default="NULL", help="Set NVMain configuration value for PARAM")
    argnum = argnum + 1

(options, args) = parser.parse_args()

# Sanity checks
if args:
    print "Error: script doesn't take any positional arguments"
    sys.exit(1)

if options.cfg == None:
    print "Error: no system config."
    sys.exit(1)

if options.simpoint_mode == "init" and options.init_checkpoint_dir == None:
    print "Error: Need --init-checkpoint-dir for init mode."
    sys.exit(1)
elif options.simpoint_mode == "fastfwd" and options.init_checkpoint_dir == None:
    print "Error: Need --init-checkpoint-dir for fastfwd mode."
    sys.exit(1)
elif options.simpoint_mode == "checkpoint":
    if options.init_checkpoint_dir == None or options.checkpoint_dir == None:
        print "Error: Need --init-checkpoint-dir and --checkpoint-dir for checkpoint mode"
        sys.exit(1)
elif options.simpoint_mode == "simulate" and options.checkpoint_dir == None:
    print "Error: Need --checkpoint-dir for simulation mode."
    sys.exit(1)

if options.isolated_cpus != None:
    isolated_cpu_list = options.isolated_cpus.split(',')

    # Basic sanity check, it's up to the user to not have duplicates.
    # Hopefully linux prints an error in that case.
    for isolated_cpu in isolated_cpu_list:
        if int(isolated_cpu) > options.num_cpus or int(isolated_cpu) < 0:
            print "Tried to isolate CPU %s, but there are only %d cpus" % (isolated_cpu, options.num_cpus)
            sys.exit(1)

    # Is this an error? Let linux decide
    if len(isolated_cpu_list) == options.num_cpus:
        print "Warning: All CPUs are isolated!"

# Parse benchmark option
simpoint_list = []
if options.simpoint_mode == "checkpoint" or options.simpoint_mode == "fastfwd":
    bench_list = options.benchmark.split(':')
    fsBench_list = []
    simpoint_inst_list = []

    for bench in bench_list:
        specBench = spec_fs.getSPECFSBench(bench)
        fsBench_list.append(specBench)
        print "Benchmark %s starts at %d" % (bench, specBench.getSimpoint())
        if not specBench.getSimpoint() in simpoint_list:
            simpoint_list.append(specBench.getSimpoint())

    sorted_points = sorted(fsBench_list, key=operator.attrgetter('simpoint'))
    sorted_points.reverse()

    max_simpoint_inst = max(simpoint_list)
    for point in sorted_points:
        next_inst = max_simpoint_inst - point.getSimpoint()
        if not next_inst in simpoint_inst_list:
            simpoint_inst_list.append(next_inst)
        point.setStartInst(next_inst)

    print "Starting benchmarks at %d inst counts:" % len(simpoint_inst_list)
    for inst in simpoint_inst_list:
        print inst

    for point in sorted_points:
        print "Bench %s starting at inst %d (simpoint is %d)" % (point.getCmd(), point.getStartInst(), point.getSimpoint())

# Setup base machine
bm = [SysConfig(disk=options.disk_image, mem=options.mem_size)]

# At the moment simulation always begins in atomic. Simulate mode will
# quickly switch into a timing CPU
sim_mem_mode = "atomic"

#test_sys = makeLinuxX86System(sim_mem_mode, options.num_cpus, bm[0])

test_sys = makeArmSystem(sim_mem_mode, options.machine_type, bm[0],
                                 options.dtb_filename,
                                 bare_metal=options.bare_metal)
# Add isolated CPUs option if used
if options.isolated_cpus != None:
    test_sys.boot_osflags = "%s isolcpus=%s" % (test_sys.boot_osflags, options.isolated_cpus)

# Voltage and Clock Domains
test_sys.voltage_domain = VoltageDomain(voltage = options.sys_voltage)
test_sys.clk_domain = SrcClockDomain(clock =  options.sys_clock,
                                     voltage_domain = test_sys.voltage_domain)
test_sys.cpu_voltage_domain = VoltageDomain()
test_sys.cpu_clk_domain = SrcClockDomain(clock = options.cpu_clock,
                                         voltage_domain =
                                         test_sys.cpu_voltage_domain)

if options.kernel is not None:
    test_sys.kernel = binary(options.kernel)

if options.script is not None:
    test_sys.readfile = options.script

test_sys.init_param = options.init_param

# Parse system config file
config = ConfigParser.RawConfigParser()
config.optionxform = str
config.read(options.cfg)

config.remove_option('cpu', 'type')

# For now, assign all the CPUs to the same clock domain
np = options.num_cpus

test_sys.cpu = [AtomicSimpleCPU(clk_domain=test_sys.cpu_clk_domain, cpu_id=i, switched_out=False) for i in xrange(np)]

for i in xrange(np):
    test_sys.cpu[i].createThreads()
    if options.simpoint_mode == "checkpoint" or options.simpoint_mode == "fastfwd":
        # This is meant to get to the last simpoint. Not sure what will happen if
        # the simpoint is instruction 0.
        test_sys.cpu[i].max_insts_all_threads = max(simpoint_list)

if options.simpoint_mode == "simulate" or options.simpoint_mode == "fastfwd" or options.simpoint_mode == "batch":
    cpu_options = dict(config.items('cpu'))
    simulate_cpu = [O3_ARM_v7a_3(clk_domain=test_sys.cpu_clk_domain, cpu_id=i, switched_out=True, **cpu_options) for i in xrange(np)]
    for i in xrange(np):
        simulate_cpu[i].workload = test_sys.cpu[i].workload
        if options.max_insts:
            #test_sys.cpu[i].max_insts_all_threads = options.max_insts
            simulate_cpu[0].max_insts_all_threads = options.max_insts

    switch_cpu_list = [(test_sys.cpu[i], simulate_cpu[i]) for i in xrange(np)]
    test_sys.switch_cpu = simulate_cpu

if options.simpoint_mode == "checkpoint" or options.simpoint_mode == "fastfwd":
    # We need a reference CPU to see how many instructions were run.
    ref_cpu = 0

    # If we are using isolated CPUs, choose the first one as the reference
    if options.isolated_cpus != None:
        ref_cpu = int(options.isolated_cpus.split(',')[0])

    test_sys.cpu[ref_cpu].simpoint_start_insts = simpoint_inst_list

#test_sys.iobridge = Bridge(delay='50ns', ranges = test_sys.mem_ranges)
test_sys.iocache = IOCache(addr_ranges = test_sys.mem_ranges)
test_sys.iocache.cpu_side = test_sys.iobus.master
test_sys.iocache.mem_side = test_sys.membus.slave

# Configure L2 cache
if config.has_section('l2') and not options.private_l2:
    l2_options = dict(config.items('l2'))
    if l2_options.has_key('prefetcher'):
        l2_options['prefetcher'] = eval(l2_options['prefetcher'])
    test_sys.l2 = BaseCache(clk_domain = test_sys.cpu_clk_domain, **l2_options)
    test_sys.tol2bus = CoherentXBar(clk_domain = test_sys.cpu_clk_domain, width = 64)
    test_sys.l2.cpu_side = test_sys.tol2bus.master
    if config.has_section('l3') == False:
        test_sys.l2.mem_side = test_sys.membus.slave
elif config.has_section('l2') and options.private_l2:
    l2_options = dict(config.items('l2'))
    if l2_options.has_key('prefetcher'):
        l2_options['prefetcher'] = eval(l2_options['prefetcher'])
    test_sys.l2 = [BaseCache(clk_domain = test_sys.cpu_clk_domain, **l2_options) for i in xrange(np)]
    test_sys.tol2bus = [CoherentBus(clk_domain = test_sys.cpu_clk_domain, width = 32) for i in xrange(np)]
    for idx in xrange(np):
        test_sys.l2[idx].cpu_side = test_sys.tol2bus[idx].master

# Configure L3 cache
if config.has_section('l3'):
    l3_options = dict(config.items('l3'))
    if l3_options.has_key('prefetcher'):
        l3_options['prefetcher'] = eval(l3_options['prefetcher'])
    test_sys.l3 = BaseCache(clk_domain = test_sys.cpu_clk_domain, **l3_options)
    test_sys.tol3bus = CoherentBus(clk_domain = test_sys.clk_domain, width = 16)
    if not options.private_l2:
        test_sys.l2.mem_side = test_sys.tol3bus.slave
    else:
        for idx in xrange(np):
            test_sys.l2[idx].mem_side = test_sys.tol3bus.slave
    test_sys.l3.cpu_side = test_sys.tol3bus.master
    test_sys.l3.mem_side = test_sys.membus.slave

for i in xrange(options.num_cpus):
    icache = None
    if config.has_section('icache') == False:
        print "Error: no icache defined."
        sys.exit(1)
    icache_options = dict(config.items('icache'))
    if icache_options.has_key('prefetcher'):
        icache_options['prefetcher'] = eval(icache_options['prefetcher'])
    icache = BaseCache(**icache_options)

    dcache = None
    if config.has_section('dcache') == False:
        print "Error: no dcache defined."
        sys.exit(1)
    dcache_options = dict(config.items('dcache'))
    if dcache_options.has_key('prefetcher'):
        dcache_options['prefetcher'] = eval(dcache_options['prefetcher'])
    dcache = BaseCache(**dcache_options)

    if buildEnv['TARGET_ISA'] == 'x86':
        test_sys.cpu[i].addPrivateSplitL1Caches(icache, dcache,
                                              PageTableWalkerCache(),
                                              PageTableWalkerCache())
    else:
        test_sys.cpu[i].addPrivateSplitL1Caches(icache, dcache)
    test_sys.cpu[i].createInterruptController()

    if config.has_section('l2'):
        if not options.private_l2:
            test_sys.cpu[i].connectAllPorts(test_sys.tol2bus, test_sys.membus)
        else:
            test_sys.cpu[i].connectAllPorts(test_sys.tol2bus[i], test_sys.membus)
    else:
        test_sys.cpu[i].connectAllPorts(test_sys.membus)


MemConfig.config_mem(options, test_sys)

root = Root(full_system=True, system=test_sys)

checkpoint_dir = None
if options.simpoint_mode == "checkpoint" or options.simpoint_mode == "fastfwd":
    checkpoint_dir = os.path.join(options.init_checkpoint_dir, "cpt.init")
elif options.simpoint_mode == "simulate" or options.simpoint_mode == "check_affinity":
    checkpoint_dir = os.path.join(options.checkpoint_dir, "cpt.%s" % options.benchmark.replace(':', '_'))
elif options.simpoint_mode == "batch":
    checkpoint_dir = os.path.join(options.checkpoint_dir, "")
m5.instantiate(checkpoint_dir)

#term_port = test_sys.pc.com_1.terminal.getListenPort()
#print 'term port %d' % (test_sys.terminal.getListenPort())
term_port = test_sys.terminal.getListenPort()

print "**** REAL SIMULATION ****"

start_count = 0
maxtick = m5.MaxTick

if options.simpoint_mode == "init":
    (term, inpipe) = pyterm.pyterm(term_port)
elif options.simpoint_mode == "checkpoint" or options.simpoint_mode == "fastfwd":
    (term, inpipe) = pyterm.pyterm(term_port)

    print "Waiting for bash shell to start..."

    exit_event = m5.simulate(m5.curTick() + 100000000000)
    exit_cause = exit_event.getCause()

    print "Wait stopped because %s" % exit_cause

    print "Starting longest simpoint benchmark(s) on CPU0"

    for bench in sorted_points:
        if bench.getStartInst() == 0:
            start_cpu = start_count

            # Start on an isolated_cpu..
            if options.isolated_cpus != None:
                isolated_cpu_list = options.isolated_cpus.split(',')
                start_cpu = int(isolated_cpu_list[start_count % len(isolated_cpu_list)])

            print "Starting benchmark %s on CPU %d" % (bench.getCmd(), start_cpu)
            inpipe.send(spec_fs.getSPECCmd(bench, start_cpu))
            inpipe.send("export PID%i=$!\n" % start_count)
            start_count = start_count + 1

    if start_count >= len(sorted_points) and options.simpoint_mode == "checkpoint":
        print "Sending checkpoint write (deferred) -- All at 0"

        stop_cmd = "kill -s SIGSTOP "
        for pid in xrange(len(options.benchmark.split(':'))):
            stop_cmd = "%s $PID%i" % (stop_cmd, pid)
        #inpipe.send("%s\n" % stop_cmd)
        #inpipe.send("/sbin/m5 checkpoint 1000000\n")
        #while exit_cause != "checkpoint":
        exit_event = m5.simulate()
        exit_cause = exit_event.getCause()

        print 'Exiting @ tick %i because %s' % (m5.curTick(), exit_cause)
        while exit_cause != "all threads reached the max instruction count":
            exit_event = m5.simulate()
            exit_cause = exit_event.getCause()
        print 'Exiting @ tick %i because %s' % (m5.curTick(), exit_cause)
        inpipe.send("/sbin/m5 checkpoint\n")
        print 'here'
        while exit_cause != "checkpoint":
            exit_event = m5.simulate()
            exit_cause = exit_event.getCause()
        if exit_cause == "checkpoint":
            mkdir_p(options.checkpoint_dir)
            m5.checkpoint(os.path.join(options.checkpoint_dir, "cpt.%s" % options.benchmark.replace(':', '_')))
        pyterm.close_pyterm(term, inpipe)

        print 'Exiting @ tick %i because %s' % (m5.curTick(), exit_event.getCause())
        if not m5.options.interactive:
            sys.exit(exit_event.getCode())
        sys.exit(0)
    elif start_count >= len(sorted_points) and options.simpoint_mode =="fastfwd":
        inpipe.send("/sbin/m5 switchcpus\n")

        exit_event = m5.simulate()
        exit_cause = exit_event.getCause()

        if exit_cause == "switch cpus":
            print "Done fast-forwarding -- Switching to detailed CPU"

            m5.switchCpus(test_sys, switch_cpu_list)
        else:
            print "exit_cause was %s" % exit_cause
            sys.exit(1)

elif options.simpoint_mode == "simulate" or options.simpoint_mode == "batch":
    (term, inpipe) = pyterm.pyterm(term_port)

    print "Waiting for bash shell to start (tick %i)..." % m5.curTick()

    exit_event = m5.simulate(10000000)
    #exit_event = m5.simulate(10000000000)
    exit_cause = exit_event.getCause()

    print "Wait stopped because %s" % exit_cause
    print "Switching CPUS at tick %s" % m5.curTick()

    # For some reason if we restore with a detailed CPU linux
    # crashes with a bad page state error
    m5.switchCpus(test_sys, switch_cpu_list)

    cont_cmd = "kill -s SIGCONT "
    for pid in xrange(len(options.benchmark.split(':'))):
        cont_cmd = "%s $PID%i" % (cont_cmd, pid)
    #inpipe.send("%s\n" % cont_cmd)
    if options.simpoint_mode == "batch":
        bench_list = options.benchmark.split(':')
        fsBench_list = []
        for bench in bench_list:
            print "bench is %s" % bench
            inpipe.send(spec_fs.getSPECCmd(bench, 0))

    inpipe.send("echo Affirmative\n")
elif options.simpoint_mode == "check_affinity":
    (term, inpipe) = pyterm.pyterm(term_port)

    print "Waiting for bash shell to start (tick %i)..." % m5.curTick()

    exit_event = m5.simulate(10000000000)
    exit_cause = exit_event.getCause()

    print "Wait stopped because %s" % exit_cause

    inpipe.send("mount -t proc proc /proc\n")
    inpipe.send("ps -el\n")
    inpipe.send("cat < /sys/kernel/debug/palloc/palloc_mask\n")
    inpipe.send("/sbin/m5 exit\n")

    exit_event = m5.simulate(m5.curTick() + 10000000000)
    exit_cause = exit_event.getCause()

    pyterm.close_pyterm(term, inpipe)
    sys.exit(0)

exit_event = m5.simulate(maxtick - m5.curTick())
exit_cause = exit_event.getCause()
print 'Exiting @ tick %i because %s maxtick %s' % (m5.curTick(), exit_event.getCause(),maxtick)
#while exit_cause == "all threads reached the max instruction count":
#    exit_event = m5.simulate(maxtick - m5.curTick())
#    exit_cause = exit_event.getCause()

if options.simpoint_mode == "init":
    if exit_cause == "checkpoint":
        mkdir_p(options.init_checkpoint_dir)
        m5.checkpoint(os.path.join(options.init_checkpoint_dir, "cpt.init"))
    pyterm.close_pyterm(term, inpipe)
elif options.simpoint_mode == "checkpoint" or options.simpoint_mode == "fastfwd":
    num_inst_steps = 0
    max_inst_steps = len(simpoint_list)

    while exit_cause == "simpoint starting point found":
        m5.stats.dump()

        num_inst_steps = num_inst_steps + 1

        if num_inst_steps >= max_inst_steps:
            exit_cause = "%d simpoints aligned" % len(bench_list)
            break

        cur_inst = simpoint_inst_list[num_inst_steps]
        print "Current inst should be %d" % simpoint_list[num_inst_steps]

        for bench in sorted_points:
            if bench.getStartInst() == cur_inst:
                start_cpu = start_count % options.num_cpus

                # Start on an isolated_cpu..
                if options.isolated_cpus != None:
                    isolated_cpu_list = options.isolated_cpus.split(',')
                    start_cpu = int(isolated_cpu_list[start_count % len(isolated_cpu_list)])

                print "Starting benchmark %s on CPU %d" % (bench.getCmd(), start_cpu)
                inpipe.send(spec_fs.getSPECCmd(bench, start_cpu))
                inpipe.send("export PID%i=$!\n" % start_count)
                start_count = start_count + 1

        if start_count >= len(sorted_points):
            # Continue until max instruction...
            print "Here..............................."
            exit_event = m5.simulate()
            exit_cause = exit_event.getCause()

            if exit_cause != "all threads reached the max instruction count":
                print "WARNING: Expected max instruction count exit, but the cause was: %s" % exit_cause
                print "Continuing anyways..."

            if options.simpoint_mode == "fastfwd":
                break

            print "Sending checkpoint write (deferred)"

            stop_cmd = "kill -s SIGSTOP "
            for pid in xrange(len(options.benchmark.split(':'))):
                stop_cmd = "%s $PID%i" % (stop_cmd, pid)
            #inpipe.send("%s\n" % stop_cmd)
            inpipe.send("/sbin/m5 checkpoint 1000000\n")
            while exit_cause != "checkpoint":
                exit_event = m5.simulate()
                exit_cause = exit_event.getCause()

        if exit_cause == "checkpoint":
            m5.checkpoint(os.path.join(options.checkpoint_dir, "cpt.%s" % options.benchmark.replace(':', '_')))

        assert exit_cause is not "simpoint starting point found"

    if options.simpoint_mode == "fastfwd":
        m5.switchCpus(test_sys, switch_cpu_list)

        print "*** FAST FORWARD FINISHED ***"

        exit_event = m5.simulate(maxtick - m5.curTick())
        exit_cause = exit_event.getCause()

    pyterm.close_pyterm(term, inpipe)
elif options.simpoint_mode == "simulate" or options.simpoint_mode == "batch":
    pyterm.close_pyterm(term, inpipe)

print 'Exiting @ tick %i because %s' % (m5.curTick(), exit_event.getCause())
if not m5.options.interactive:
    sys.exit(exit_event.getCode())

