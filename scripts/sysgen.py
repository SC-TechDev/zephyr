#! /usr/bin/env python
#
# sysgen.py - System Generator
#
#
# Copyright (c) 2015, Wind River Systems, Inc.
#
# Redistribution and use in source and binary forms, with or without
# modification, are permitted provided that the following conditions are met:
#
# 1) Redistributions of source code must retain the above copyright notice,
# this list of conditions and the following disclaimer.
#
# 2) Redistributions in binary form must reproduce the above copyright notice,
# this list of conditions and the following disclaimer in the documentation
# and/or other materials provided with the distribution.
#
# 3) Neither the name of Wind River Systems nor the names of its contributors
# may be used to endorse or promote products derived from this software without
# specific prior written permission.
#
# THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDERS AND CONTRIBUTORS "AS IS"
# AND ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT LIMITED TO, THE
# IMPLIED WARRANTIES OF MERCHANTABILITY AND FITNESS FOR A PARTICULAR PURPOSE
# ARE DISCLAIMED. IN NO EVENT SHALL THE COPYRIGHT HOLDER OR CONTRIBUTORS BE
# LIABLE FOR ANY DIRECT, INDIRECT, INCIDENTAL, SPECIAL, EXEMPLARY, OR
# CONSEQUENTIAL DAMAGES (INCLUDING, BUT NOT LIMITED TO, PROCUREMENT OF
# SUBSTITUTE GOODS OR SERVICES; LOSS OF USE, DATA, OR PROFITS; OR BUSINESS
# INTERRUPTION) HOWEVER CAUSED AND ON ANY THEORY OF LIABILITY, WHETHER IN
# CONTRACT, STRICT LIABILITY, OR TORT (INCLUDING NEGLIGENCE OR OTHERWISE)
# ARISING IN ANY WAY OUT OF THE USE OF THIS SOFTWARE, EVEN IF ADVISED OF THE
# POSSIBILITY OF SUCH DAMAGE.
#

# Required arguments:
#   - name of VPF file

# Generates:
#   - kernel_main.c file
#   - microkernel_objects.h file
#   - vxmicro.h file

import os
import sys

# input-related variables

num_kargs = 0
num_timers = 0

task_list = []
event_list = []
mutex_list = []
sema_list = []
fifo_list = []
pipe_list = []
mbx_list = []
map_list = []
pool_list = []

driver_list = []

group_dictionary = {}
group_key_list = []

# output-related variables

kernel_main_c_data = ""
vxmicro_h_data = ""
micro_objs_h_data = ""


def get_output_dir():
    if len(sys.argv) > 2:
        return sys.argv[2]
    else:
        return ""

output_dir = get_output_dir()


def vpf_parse():
    """ Parse VPF file """

    global num_kargs
    global num_timers

    # open file for reading
    with open(sys.argv[1], 'r') as infile:

        # read file contents
        data = infile.read()

    # create list of the lines, breaking at line boundaries
    my_list = data.splitlines()

    # process each line
    for line in my_list:
        words = line.split()

        if (len(words) == 0):
            continue    # ignore blank line

        if (words[0][0] == "%"):
            continue    # ignore comment line

        if (words[0] == "CONFIG"):
            num_kargs = int(words[1])
            num_timers = int(words[2])
            continue

        if (words[0] == "TASK"):
            task_list.append((words[1], int(words[2]), words[3],
                              int(words[4]), words[5]))
            continue

        if (words[0] == "TASKGROUP"):
            if words[1] in group_dictionary:
                continue    # ignore re-definition of a task group
            group_bitmask = 1 << len(group_dictionary)
            group_dictionary[words[1]] = group_bitmask
            group_key_list.append(words[1])
            continue

        if (words[0] == "EVENT"):
            event_list.append((words[1], words[2]))
            continue

        if (words[0] == "SEMA"):
            sema_list.append((words[1],))
            continue

        if (words[0] == "MUTEX"):
            mutex_list.append((words[1],))
            continue

        if (words[0] == "FIFO"):
            fifo_list.append((words[1], int(words[2]), int(words[3])))
            continue

        if (words[0] == "PIPE"):
            pipe_list.append((words[1], int(words[2])))
            continue

        if (words[0] == "MAILBOX"):
            mbx_list.append((words[1],))
            continue

        if (words[0] == "MAP"):
            map_list.append((words[1], int(words[2]), int(words[3])))
            continue

        if (words[0] == "POOL"):
            pool_list.append((words[1], int(words[2]), int(words[3]),
                              int(words[4])))
            continue

        if (words[0] == "TIMERDRIVER"):
            start_quote = line.find("'")
            end_quote = line.rfind("'")
            driver_list.append(line[start_quote + 1:end_quote])
            continue

        if (words[0] == "USERDRIVER"):
            start_quote = line.find("'")
            end_quote = line.rfind("'")
            driver_list.append(line[start_quote + 1:end_quote])
            continue

        print "UNRECOGNIZED INPUT LINE"
        print words     # display any unrecognized line

# Generate miscellaneous global variables

kernel_main_c_filename_str = \
    "/* kernel_main.c - microkernel mainline and kernel objects */\n\n"

do_not_edit_warning = \
    "\n\n\n/* THIS FILE IS AUTOGENERATED -- DO NOT MODIFY! */\n\n\n"

copyright = \
    "/*\n" + \
    " * Copyright (c) 2015 Wind River Systems, Inc.\n" + \
    " *\n" + \
    " * Redistribution and use in source and binary forms," + \
    " with or without\n" + \
    " * modification, are permitted provided that the following conditions" + \
    " are met:\n" + \
    " *\n" + \
    " * 1) Redistributions of source code must retain" + \
    " the above copyright notice,\n" + \
    " * this list of conditions and the following disclaimer.\n" + \
    " *\n" + \
    " * 2) Redistributions in binary form must reproduce" + \
    " the above copyright notice,\n" + \
    " * this list of conditions and the following disclaimer" + \
    " in the documentation\n" + \
    " * and/or other materials provided with the distribution.\n" + \
    " *\n" + \
    " * 3) Neither the name of Wind River Systems nor the names" + \
    " of its contributors\n" + \
    " * may be used to endorse or promote products derived" + \
    " from this software without\n" + \
    " * specific prior written permission.\n" + \
    " *\n" + \
    " * THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDERS" + \
    " AND CONTRIBUTORS \"AS IS\"\n" + \
    " * AND ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING," + \
    " BUT NOT LIMITED TO, THE\n" + \
    " * IMPLIED WARRANTIES OF MERCHANTABILITY AND FITNESS" + \
    " FOR A PARTICULAR PURPOSE\n" + \
    " * ARE DISCLAIMED. IN NO EVENT SHALL THE COPYRIGHT HOLDER" + \
    " OR CONTRIBUTORS BE\n" + \
    " * LIABLE FOR ANY DIRECT, INDIRECT, INCIDENTAL, SPECIAL," + \
    " EXEMPLARY, OR\n" + \
    " * CONSEQUENTIAL DAMAGES (INCLUDING, BUT NOT LIMITED TO," + \
    " PROCUREMENT OF\n" + \
    " * SUBSTITUTE GOODS OR SERVICES; LOSS OF USE, DATA, OR PROFITS;" + \
    " OR BUSINESS\n" + \
    " * INTERRUPTION) HOWEVER CAUSED AND ON ANY THEORY OF LIABILITY," + \
    " WHETHER IN\n" + \
    " * CONTRACT, STRICT LIABILITY, OR TORT" + \
    " (INCLUDING NEGLIGENCE OR OTHERWISE)\n" + \
    " * ARISING IN ANY WAY OUT OF THE USE OF THIS SOFTWARE," + \
    " EVEN IF ADVISED OF THE\n" + \
    " * POSSIBILITY OF SUCH DAMAGE.\n" + \
    " */\n"


def kernel_main_c_general():
    kernel_main_c_out(
        kernel_main_c_filename_str +
        copyright +
        do_not_edit_warning +
        "\n" +
        "#include <microkernel.h>\n" +
        "#include <k_boot.h>\n" +
        "#include <toolchain.h>\n" +
        "#include <sections.h>\n" +
        "#include <vxmicro.h>")

    kernel_main_c_out("\nconst knode_t K_ThisNode = 0x00010000;")
    kernel_main_c_out(
        "\nchar __noinit _minik_stack[CONFIG_MICROKERNEL_SERVER_STACK_SIZE];")
    kernel_main_c_out(
        "int K_StackSize = CONFIG_MICROKERNEL_SERVER_STACK_SIZE;")


def kernel_main_c_kargs():
    """ Generate command packet variables """

    # command packets

    kernel_main_c_out("\n" +
        "struct k_args K_ArgsBlocks[%s] =\n" % (num_kargs) +
        "{\n" +
        "    {NULL, NULL, 0, 0, 0, (K_COMM) UNDEFINED},")
    for i in range(1, num_kargs - 1):
        kernel_main_c_out(
            "    {&K_ArgsBlocks[%d], NULL, 0, 0, 0, (K_COMM) UNDEFINED}," %
            (i - 1))
    kernel_main_c_out(
        "    {&K_ArgsBlocks[%d], NULL, 0, 0, 0, (K_COMM) UNDEFINED}" %
        (num_kargs - 2) +
        "\n};")

    # linked list of free command packets

    kernel_main_c_out("\n" +
        "struct nano_lifo K_ArgsFree = " +
        "{(void *) &K_ArgsBlocks[%d], NULL};" % (num_kargs - 1))


def kernel_main_c_timers():
    """ Generate timer system variables """

    # timer descriptors

    kernel_main_c_out("\n" +
        "K_TIMER K_TimerBlocks[%d] =\n" % (num_timers) +
        "{\n" +
        "    {NULL, NULL, 0, 0, (struct k_args *)0xffffffff},")
    for i in range(1, num_timers - 1):
        kernel_main_c_out(
            "    {&K_TimerBlocks[%d], NULL, 0, 0, " % (i - 1) +
            "(struct k_args *)0xffffffff},")
    kernel_main_c_out(
        "    {&K_TimerBlocks[%d], NULL, 0, 0, (struct k_args *)0xffffffff}\n" %
        (num_timers - 2) +
        "};")

    # linked list of free timers

    kernel_main_c_out("\n" +
        "struct nano_lifo K_TimerFree = " +
        "{(void *) &K_TimerBlocks[%d], NULL};" % (num_timers - 1))


def kernel_main_c_tasks():
    """ Generate task variables """

    total_tasks = len(task_list) + 1

    # task global variables

    kernel_main_c_out("int K_TaskCount = %d;" % (total_tasks - 1))

    # task stack areas

    kernel_main_c_out("")
    for task in task_list:
        kernel_main_c_out("char __noinit __%s_stack[%d];" % (task[0], task[3]))

    # task descriptors (including one for idle task)

    kernel_main_c_out("\n" +
        "struct k_proc K_TaskList[%d] =\n" % (total_tasks) +
        "{")
    ident = 0x00010000
    for task in task_list:
        prio = task[1]
        entry = task[2]
        size = task[3]

        stack = "__" + task[0] + "_stack"

        # create bitmask of group(s) task belongs to
        group_bitmask = 0
        group_set = task[4][1:len(task[4]) - 1]   # drop [] surrounding groups
        if (group_set != ""):
            group_list = group_set.split(',')
            for group in group_list:
                group_bitmask |= group_dictionary[group]

        # invert bitmask to convert SYS indication to non-SYS indication
        #
        # NOTE: There actually is no SYS group; instead, there is a non-SYS
        # group that all tasks belong to unless they specify the 'SYS' name.
        # This approach allows the kernel to easily suspend all non-SYS tasks
        # during debugging, while minimizing the number of task entries that
        # have to explicitly indicate their SYS/non-SYS status.
        group_bitmask ^= group_dictionary['SYS']

        kernel_main_c_out(
            "    {NULL, NULL, %d, %#010x, " % (prio, ident) +
            "0x00000001, %#010x,\n" % (group_bitmask) +
            "%s, %s, %d, (taskabortfunction)NULL}," % (entry, stack, size))
        ident += 1

    kernel_main_c_out("    {NULL, NULL, 63, 0x00000000, " +
        "0x00000000, 0x00000000,\n" +
        "(taskstartfunction)NULL, NULL, 0, (taskabortfunction)NULL}")
    kernel_main_c_out("};")

    # currently scheduled task (idle task)

    kernel_main_c_out("\n" +
        "struct k_proc * K_Task = &K_TaskList[%d];" % (total_tasks - 1))


def kernel_main_c_priorities():
    """ Generate task scheduling variables """

    num_prios = 64
    total_tasks = len(task_list) + 1

    # priority queue descriptors (lowest priority queue contains idle task)

    kernel_main_c_out("\n" +
        "struct k_tqhd K_PrioList[%d] =\n" % (num_prios) +
        "{")
    for i in range(1, num_prios):
        kernel_main_c_out(
            "    {NULL, (struct k_proc *)&K_PrioList[%d]}," % (i - 1))
    kernel_main_c_out(
        "    {&K_TaskList[%d], &K_TaskList[%d]}\n" %
        (total_tasks - 1, total_tasks - 1) +
        "};")

    # active priority queue (idle task's queue)

    kernel_main_c_out("\n" +
        "struct k_tqhd * K_Prio = &K_PrioList[%d];" % (num_prios - 1))


def kernel_main_c_events():
    """ Generate event variables """

    total_events = 4 + len(event_list)

    # event descriptors

    kernel_main_c_out("\n" +
        "struct evstr EVENTS[%d] =\n" % (total_events) +
        "{")
    # pre-defined events
    kernel_main_c_out(
        "    {0, (kevent_handler_t)K_ticker, (struct k_args *)NULL, 0},\n" +
        "    {0, (kevent_handler_t)NULL, (struct k_args *)NULL, 0},\n" +
        "    {0, (kevent_handler_t)NULL, (struct k_args *)NULL, 0},\n" +
        "    {0, (kevent_handler_t)NULL, (struct k_args *)NULL, 0},"
    )
    # project-specific events
    for event in event_list:
        kernel_main_c_out(
            "    {0, (kevent_handler_t)%s, (struct k_args *)NULL, 0}," %
            (event[1]))
    kernel_main_c_out("};")

    # number of events

    kernel_main_c_out("\n" +
        "const int K_max_eventnr = %d;" % (total_events))

    # event object identifiers

    kernel_main_c_out("")

    for event_name in event_list:
        kernel_main_c_out(
            "const kevent_t %s_objId = %s;" %
            (event_name[0], event_name[0]))


def kernel_main_c_mutexes():
    """ Generate mutex variables """

    total_mutexes = len(mutex_list)

    if (total_mutexes == 0):
        kernel_main_c_out("\nstruct mutex_struct * K_MutexList = NULL;")
        return

    # mutex descriptors

    kernel_main_c_out("\n" +
        "struct mutex_struct K_MutexList[%s] =\n" % (total_mutexes) +
        "{")
    for mutex in mutex_list:
        kernel_main_c_out("    {ANYTASK, 64, 64, 0, NULL, 0, 0},")
    kernel_main_c_out("};")
    kernel_main_c_out("")

    # mutex object identifiers

    for mutex in mutex_list:
        name = mutex[0]
        kernel_main_c_out("const kmutex_t %s_objId = %s;" % (name, name))


def kernel_main_c_semas():
    """ Generate semaphore variables """

    total_semas = len(sema_list)

    if (total_semas == 0):
        kernel_main_c_out("\nstruct sem_struct * K_SemList = NULL;")
        return

    # semaphore descriptors

    kernel_main_c_out("\n" +
        "struct sem_struct K_SemList[%s] =\n" % (total_semas) +
        "{")
    for semaphore in sema_list:
        kernel_main_c_out("    {NULL, 0, 0},")
    kernel_main_c_out("};")


def kernel_main_c_fifos():
    """ Generate FIFO variables """

    total_fifos = len(fifo_list)

    if (total_fifos == 0):
        kernel_main_c_out("\nstruct que_struct * K_QueList = NULL;")
        return

    # FIFO buffers

    kernel_main_c_out("")

    for fifo in fifo_list:
        kernel_main_c_out(
            "char __noinit __%s_buffer[%d];" % (fifo[0], fifo[1] * fifo[2]))

    # FIFO descriptors

    kernel_main_c_out("\n" +
        "struct que_struct K_QueList[%s] =\n" % (total_fifos) +
        "{"
    )
    for fifo in fifo_list:
        depth = fifo[1]
        width = fifo[2]
        buffer = "__" + fifo[0] + "_buffer"
        kernel_main_c_out(
            "    {%d, %d, %s, %s + (%d * %d),\n" %
            (depth, width, buffer, buffer, depth, width) +
            "%s, %s, NULL, 0, 0, 0}," %
            (buffer, buffer))
    kernel_main_c_out("};")


def kernel_main_c_pipes():
    """ Generate pipe variables """

    total_pipes = len(pipe_list)

    # pipe global variables

    kernel_main_c_out("int K_PipeCount = %d;" % (total_pipes))

    if (total_pipes == 0):
        kernel_main_c_out("\nstruct pipe_struct * K_PipeList = NULL;")
        return

    # pipe buffers

    kernel_main_c_out("")

    for pipe in pipe_list:
        kernel_main_c_out(
            "char __noinit __%s_buffer[%d];" % (pipe[0], pipe[1]))

    # pipe descriptors

    kernel_main_c_out("\n" +
        "struct pipe_struct K_PipeList[%d] =\n" % (total_pipes) +
        "{")
    for pipe in pipe_list:
        size = pipe[1]
        buffer = "__" + pipe[0] + "_buffer"
        kernel_main_c_out("    {%d, %s}," % (size, buffer))
    kernel_main_c_out("};")

    # pipe variables [should probably be eliminated]

    kernel_main_c_out("\n" +
        "PFN_CHANNEL_RW  pHS_Channel_Put = (PFN_CHANNEL_RW)NULL;\n" +
        "PFN_CHANNEL_RW  pHS_Channel_PutW = (PFN_CHANNEL_RW)NULL;\n" +
        "PFN_CHANNEL_RWT pHS_Channel_PutWT = (PFN_CHANNEL_RWT)NULL;\n" +
        "PFN_CHANNEL_RW  pHS_Channel_Get = (PFN_CHANNEL_RW)NULL;\n" +
        "PFN_CHANNEL_RW  pHS_Channel_GetW = (PFN_CHANNEL_RW)NULL;\n" +
        "PFN_CHANNEL_RWT pHS_Channel_GetWT = (PFN_CHANNEL_RWT)NULL;\n" +
        "PFN_CHANNEL_RWT pKS_Channel_PutWT = _task_pipe_put;\n" +
        "PFN_CHANNEL_RWT pKS_Channel_GetWT = _task_pipe_get;")


def kernel_main_c_mailboxes():
    """ Generate mailbox variables """

    total_mbxs = len(mbx_list)

    if (total_mbxs == 0):
        kernel_main_c_out("\nstruct mbx_struct * K_MbxList = NULL;")
        return

    # mailbox descriptors

    kernel_main_c_out("\n" +
        "struct mbx_struct K_MbxList[%d] =\n" % (total_mbxs) +
        "{")
    for mbx in mbx_list:
        kernel_main_c_out("    {NULL, NULL, 0},")
    kernel_main_c_out("};")


def kernel_main_c_maps():
    """ Generate memory map variables """

    total_maps = len(map_list)

    # map global variables

    kernel_main_c_out("int K_MapCount = %d;" % (total_maps))

    if (total_maps == 0):
        kernel_main_c_out("\nstruct map_struct * K_MapList = NULL;")
        return

    # memory map buffers

    kernel_main_c_out("")

    for map in map_list:
        blocks = map[1]
        block_size = map[2]
        kernel_main_c_out("char __noinit __MAP_%s_buffer[%d];" %
                    (map[0], blocks * block_size))

    # memory map descriptors

    kernel_main_c_out("\nstruct map_struct K_MapList[%d] =\n{" % (total_maps))
    for map in map_list:
        blocks = map[1]
        block_size = map[2]
        kernel_main_c_out("    { %d, %d, __MAP_%s_buffer }," %
                    (blocks, block_size, map[0]))
    kernel_main_c_out("};")


def kernel_main_c_pools():
    """ Generate memory pool variables """

    total_pools = len(pool_list)

    # pool global variables

    kernel_main_c_out("\nint K_PoolCount = %d;" % (total_pools))

    if (total_pools == 0):
        kernel_main_c_out("\nstruct pool_struct * K_PoolList = NULL;")
        return

    # start accumulating memory pool descriptor info

    pool_descriptors = "\nstruct pool_struct K_PoolList[%d] =\n{\n" % \
                        (total_pools)
    ident = 0x00010000

    for pool in pool_list:

        kernel_main_c_out("")

        # create local variables relating to current pool

        min_block_size = pool[1]
        max_block_size = pool[2]
        num_maximal_blocks = pool[3]
        total_memory = max_block_size * num_maximal_blocks
        buffer = "__" + pool[0] + "_buffer"
        frag_table = "fragtab_%#010x" % ident

        # determine block sizes used by pool (including actual minimum size)

        frag_size_list = [max_block_size]
        while (ident != 0):    # loop forever
            min_block_size_actual = frag_size_list[len(frag_size_list) - 1]
            min_block_size_proposed = min_block_size_actual / 4
            if (min_block_size_proposed < min_block_size):
                break
            frag_size_list.append(min_block_size_proposed)
        frag_levels = len(frag_size_list)

        # determine size of block status arrays
        # - largest size gets special handling
        # - remainder of algorithm is a complete mystery ...

        block_status_sizes = [(num_maximal_blocks + 3) / 4]
        block_status_size_to_use = num_maximal_blocks
        for index in range(1, frag_levels):
            block_status_sizes.append(block_status_size_to_use)
            block_status_size_to_use *= 4

        # generate block status areas

        for index in range(0, frag_levels):
            kernel_main_c_out("struct block_stat blockstatus_%#010x_%d[%d];" %
                (ident, index, block_status_sizes[index]))

        # generate memory pool fragmentation descriptor

        kernel_main_c_out("\nstruct pool_block %s[%d] =\n{" %
                        (frag_table, frag_levels))
        for index in range(0, frag_levels):
            kernel_main_c_out("    { %d, %d, blockstatus_%#010x_%d}," %
                (frag_size_list[index], block_status_sizes[index],
                 ident, index))
        kernel_main_c_out("};\n")

        # generate memory pool buffer

        kernel_main_c_out("char __noinit %s[%d];" % (buffer, total_memory))

        # append memory pool descriptor info

        pool_descriptors += "    {%d, %d, 2, %d, %d, %d, NULL, %s, %s},\n" % \
            (max_block_size, min_block_size_actual, total_memory,
            num_maximal_blocks, frag_levels, frag_table, buffer)

        ident += 1

    # generate memory pool descriptor info

    pool_descriptors += "};"
    kernel_main_c_out(pool_descriptors)


def kernel_main_c_kernel_services():
    """ Generate kernel services function table """

    # initialize table with info for all possible kernel services

    func_table = [
"/*  0 */ K_nop,",                  # required
"/*  1 */ K_mvdreq,",               # required
"/*  2 */ (kernelfunc) NULL,",      # unused
"/*  3 */ (kernelfunc) NULL,",      # unused
"/*  4 */ K_offload,",              # required
"/*  5 */ K_workload,",             # required
"/*  6 */ K_signals,",              # depends on semaphores
"/*  7 */ K_signalm,",              # depends on semaphores
"/*  8 */ K_resets,",               # depends on semaphores
"/*  9 */ K_resetm,",               # depends on semaphores
"/* 10 */ K_waitsreq,",             # depends on semaphores
"/* 11 */ K_waitsrpl,",             # depends on semaphores
"/* 12 */ K_waitsrpl,",             # depends on semaphores and timers
"/* 13 */ K_waitmany,",             # depends on semaphores
"/* 14 */ K_waitmreq,",             # depends on semaphores
"/* 15 */ K_waitmrdy,",             # depends on semaphores
"/* 16 */ K_waitmcan,",             # depends on semaphores
"/* 17 */ K_waitmacc,",             # depends on semaphores
"/* 18 */ K_waitmend,",             # depends on semaphores
"/* 19 */ K_waitmtmo,",             # depends on semaphores and timers
"/* 20 */ K_inqsema,",              # depends on semaphores
"/* 21 */ K_lockreq,",              # depends on mutexes
"/* 22 */ K_lockrpl,",              # depends on mutexes
"/* 23 */ K_lockrpl,",              # depends on mutexes and timers
"/* 24 */ K_unlock,",               # depends on mutexes
"/* 25 */ K_enqreq,",               # depends on FIFOs
"/* 26 */ K_enqrpl,",               # depends on FIFOs
"/* 27 */ K_enqrpl,",               # depends on FIFOs and timers
"/* 28 */ K_deqreq,",               # depends on FIFOs
"/* 29 */ K_deqrpl,",               # depends on FIFOs
"/* 30 */ K_deqrpl,",               # depends on FIFOs and timers
"/* 31 */ K_queue,",                # depends on FIFOs
"/* 32 */ K_sendreq,",              # depends on mailboxes
"/* 33 */ K_sendrpl,",              # depends on mailboxes and timers
"/* 34 */ K_sendack,",              # depends on mailboxes
"/* 35 */ K_senddata,",             # depends on mailboxes
"/* 36 */ K_recvreq,",              # depends on mailboxes
"/* 37 */ K_recvrpl,",              # depends on mailboxes and timers
"/* 38 */ K_recvack,",              # depends on mailboxes
"/* 39 */ K_recvdata,",             # depends on mailboxes
"/* 40 */ K_elapse,",               # required
"/* 41 */ K_sleep,",                # depends on timers
"/* 42 */ K_wakeup,",               # depends on timers
"/* 43 */ K_taskop,",               # required
"/* 44 */ K_groupop,",              # required
"/* 45 */ K_set_prio,",             # required
"/* 46 */ K_yield,",                # required
"/* 47 */ K_alloc,",                # depends on memory maps
"/* 48 */ K_dealloc,",              # depends on memory maps
"/* 49 */ K_alloc_timer,",          # depends on timers
"/* 50 */ K_dealloc_timer,",        # depends on timers
"/* 51 */ K_start_timer,",          # depends on timers
"/* 52 */ K_stop_timer,",           # depends on timers
"/* 53 */ K_alloctmo,",             # depends on memory maps [and timers?]
"/* 54 */ (kernelfunc) NULL,",      # unused
"/* 55 */ (kernelfunc) NULL,",      # unused
"/* 56 */ (kernelfunc) NULL,",      # unused
"/* 57 */ (kernelfunc) NULL,",      # unused
"/* 58 */ K_event_test,",           # required
"/* 59 */ K_event_set_handler,",    # required
"/* 60 */ K_event_signal,",         # required
"/* 61 */ K_GetBlock,",             # depends on memory pools
"/* 62 */ K_RelBlock,",             # depends on memory pools
"/* 63 */ K_GetBlock_Waiters,",     # depends on memory pools
"/* 64 */ K_gtbltmo,",              # depends on memory pools
"/* 65 */ K_Defrag,",               # depends on memory pools
"/* 66 */ (kernelfunc) NULL,",      # unused
"/* 67 */ (kernelfunc) NULL,",      # unused
"/* 68 */ (kernelfunc) NULL,",      # unused
"/* 69 */ (kernelfunc) NULL,",      # unused
"/* 70 */ (kernelfunc) NULL,",      # unused
"/* 71 */ (kernelfunc) NULL,",      # unused
"/* 72 */ K_ChSendReq,",            # depends on pipes
"/* 73 */ K_ChSendTmo,",            # depends on pipes
"/* 74 */ K_ChSendRpl,",            # depends on pipes
"/* 75 */ K_ChSendAck,",            # depends on pipes
"/* 76 */ K_ChRecvReq,",            # depends on pipes
"/* 77 */ K_ChRecvTmo,",            # depends on pipes
"/* 78 */ K_ChRecvRpl,",            # depends on pipes
"/* 79 */ K_ChRecvAck,",            # depends on pipes
"/* 80 */ K_ChMovedAck,",           # depends on pipes
"/* 81 */ K_eventtesttmo"           # required
    ]

    # eliminate table entries for kernel services that project doesn't utilize
    # (note: some entries can be eliminated for more than one reason)

    if (len(sema_list) == 0):
        func_table[6] = "/*  6 */ (kernelfunc) NULL,"
        func_table[7] = "/*  7 */ (kernelfunc) NULL,"
        func_table[8] = "/*  8 */ (kernelfunc) NULL,"
        func_table[9] = "/*  9 */ (kernelfunc) NULL,"
        func_table[10] = "/* 10 */ (kernelfunc) NULL,"
        func_table[11] = "/* 11 */ (kernelfunc) NULL,"
        func_table[12] = "/* 12 */ (kernelfunc) NULL,"
        func_table[13] = "/* 13 */ (kernelfunc) NULL,"
        func_table[14] = "/* 14 */ (kernelfunc) NULL,"
        func_table[15] = "/* 15 */ (kernelfunc) NULL,"
        func_table[16] = "/* 16 */ (kernelfunc) NULL,"
        func_table[17] = "/* 17 */ (kernelfunc) NULL,"
        func_table[18] = "/* 18 */ (kernelfunc) NULL,"
        func_table[19] = "/* 19 */ (kernelfunc) NULL,"
        func_table[20] = "/* 20 */ (kernelfunc) NULL,"

    if (len(mutex_list) == 0):
        func_table[21] = "/* 21 */ (kernelfunc) NULL,"
        func_table[22] = "/* 22 */ (kernelfunc) NULL,"
        func_table[23] = "/* 23 */ (kernelfunc) NULL,"
        func_table[24] = "/* 24 */ (kernelfunc) NULL,"

    if (len(fifo_list) == 0):
        func_table[25] = "/* 25 */ (kernelfunc) NULL,"
        func_table[26] = "/* 26 */ (kernelfunc) NULL,"
        func_table[27] = "/* 27 */ (kernelfunc) NULL,"
        func_table[28] = "/* 28 */ (kernelfunc) NULL,"
        func_table[29] = "/* 29 */ (kernelfunc) NULL,"
        func_table[30] = "/* 30 */ (kernelfunc) NULL,"
        func_table[31] = "/* 31 */ (kernelfunc) NULL,"

    if (len(mbx_list) == 0):
        func_table[32] = "/* 32 */ (kernelfunc) NULL,"
        func_table[33] = "/* 33 */ (kernelfunc) NULL,"
        func_table[34] = "/* 34 */ (kernelfunc) NULL,"
        func_table[35] = "/* 35 */ (kernelfunc) NULL,"
        func_table[36] = "/* 36 */ (kernelfunc) NULL,"
        func_table[37] = "/* 37 */ (kernelfunc) NULL,"
        func_table[38] = "/* 38 */ (kernelfunc) NULL,"
        func_table[39] = "/* 39 */ (kernelfunc) NULL,"

    if (len(map_list) == 0):
        func_table[47] = "/* 47 */ (kernelfunc) NULL,"
        func_table[48] = "/* 48 */ (kernelfunc) NULL,"
        func_table[53] = "/* 53 */ (kernelfunc) NULL,"

    if (len(pool_list) == 0):
        func_table[61] = "/* 61 */ (kernelfunc) NULL,"
        func_table[62] = "/* 62 */ (kernelfunc) NULL,"
        func_table[63] = "/* 63 */ (kernelfunc) NULL,"
        func_table[64] = "/* 64 */ (kernelfunc) NULL,"
        func_table[65] = "/* 65 */ (kernelfunc) NULL,"

    if (len(pipe_list) == 0):
        func_table[72] = "/* 72 */ (kernelfunc) NULL,"
        func_table[73] = "/* 73 */ (kernelfunc) NULL,"
        func_table[74] = "/* 74 */ (kernelfunc) NULL,"
        func_table[75] = "/* 75 */ (kernelfunc) NULL,"
        func_table[76] = "/* 76 */ (kernelfunc) NULL,"
        func_table[77] = "/* 77 */ (kernelfunc) NULL,"
        func_table[78] = "/* 78 */ (kernelfunc) NULL,"
        func_table[79] = "/* 79 */ (kernelfunc) NULL,"
        func_table[80] = "/* 80 */ (kernelfunc) NULL,"

    if (num_timers == 0):
        func_table[12] = "/* 12 */ (kernelfunc) NULL,"
        func_table[19] = "/* 19 */ (kernelfunc) NULL,"
        func_table[23] = "/* 23 */ (kernelfunc) NULL,"
        func_table[27] = "/* 27 */ (kernelfunc) NULL,"
        func_table[30] = "/* 30 */ (kernelfunc) NULL,"
        func_table[33] = "/* 33 */ (kernelfunc) NULL,"
        func_table[37] = "/* 37 */ (kernelfunc) NULL,"
        func_table[41] = "/* 41 */ (kernelfunc) NULL,"
        func_table[42] = "/* 42 */ (kernelfunc) NULL,"
        func_table[49] = "/* 49 */ (kernelfunc) NULL,"
        func_table[50] = "/* 50 */ (kernelfunc) NULL,"
        func_table[51] = "/* 51 */ (kernelfunc) NULL,"
        func_table[52] = "/* 52 */ (kernelfunc) NULL,"

    # generate function table

    kernel_main_c_out("\n" +
        "const kernelfunc _minik_func[82] =\n" +
        "{")
    for func in func_table:
        kernel_main_c_out("    " + func)
    kernel_main_c_out("};")


def kernel_main_c_driver_init():
    """ Generate driver initialization routine """

    kernel_main_c_out("\n" +
        "void init_drivers(void)\n" +
        "{")
    for driver_call in driver_list:
        kernel_main_c_out("    " + driver_call + ";")
    kernel_main_c_out("}")


def kernel_main_c_node_init():
    """ Generate node initialization routine """

    kernel_main_c_out("\n" +
        "void init_node(void)\n{")
    if (len(pipe_list) > 0):
        kernel_main_c_out("    InitPipe();")
    if (len(map_list) > 0):
        kernel_main_c_out("    InitMap();")
    if (len(pool_list) > 0):
        kernel_main_c_out("    InitPools();")
    kernel_main_c_out("}")


def kernel_main_c_main():
    """ Generate main() routine """

    kernel_main_c_out("\n" +
        "void main(void)\n" +
        "{\n" +
        "    kernel_init();\n" +
        "    task_group_start(EXE);\n" +
        "    kernel_idle();\n" +
        "}")


def kernel_main_c_out(string):
    """ Append a string to kernel_main.c """

    global kernel_main_c_data

    kernel_main_c_data += string + "\n"


def write_file(filename, contents):
    """ Create file using specified name and contents """

    f = open(filename, 'w')    # overwrites it if it already exists
    f.write(contents)
    f.close()


def kernel_main_c_generate():
    """ Generate kernel_main.c file """

    global kernel_main_c_data

    # create file contents
    kernel_main_c_general()
    kernel_main_c_kargs()
    kernel_main_c_timers()
    kernel_main_c_tasks()
    kernel_main_c_priorities()
    kernel_main_c_events()
    kernel_main_c_mutexes()
    kernel_main_c_semas()
    kernel_main_c_fifos()
    kernel_main_c_pipes()
    kernel_main_c_mailboxes()
    kernel_main_c_maps()
    kernel_main_c_pools()
    kernel_main_c_kernel_services()
    kernel_main_c_driver_init()
    kernel_main_c_node_init()
    kernel_main_c_main()

    write_file(output_dir + 'kernel_main.c', kernel_main_c_data)

# Generate microkernel_objects.h file

micro_objs_h_filename_str = \
    "/* microkernel_objects.h - microkernel objects */\n\n"

micro_objs_h_include_guard = "_MICROKERNEL_OBJECTS__H_"

micro_objs_h_header_include_guard_str = \
    "#ifndef " + micro_objs_h_include_guard + "\n" \
    "#define " + micro_objs_h_include_guard + "\n\n"


def generate_micro_objs_h_header():

    global micro_objs_h_data
    micro_objs_h_data += \
        micro_objs_h_filename_str + \
        copyright + \
        do_not_edit_warning + \
        micro_objs_h_header_include_guard_str

micro_objs_h_footer_include_guard_str = \
    "\n#endif /* " + micro_objs_h_include_guard + " */\n"


def generate_micro_objs_h_footer():

    global micro_objs_h_data
    micro_objs_h_data += \
        micro_objs_h_footer_include_guard_str


def generate_taskgroup_line(taskgroup, group_id):

    global micro_objs_h_data
    micro_objs_h_data += \
        "#define " + taskgroup + " 0x%8.8x\n" % group_id


def generate_micro_objs_h_taskgroups():

    for group in group_key_list:
        generate_taskgroup_line(group, group_dictionary[group])


def generate_micro_objs_h_nodes():

    global micro_objs_h_data
    micro_objs_h_data += \
        "\n#define NODE1 0x00010000\n\n"


def generate_obj_id_line(name, obj_id):

    return "#define " + name + " 0x0001%4.4x\n" % obj_id


def generate_obj_id_lines(obj_types):

    data = ""
    for obj_type in obj_types:
        for obj in obj_type[0]:
            data += generate_obj_id_line(str(obj[0]), obj_type[1])
            obj_type[1] += 1
        if obj_type[1] > 0:
            data += "\n"

    return data


def generate_micro_objs_h_obj_ids():

    global micro_objs_h_data

    obj_types = [
        [task_list,  0],
        [mutex_list, 0],
        [sema_list,  0],
        [fifo_list,  0],
        [pipe_list,  0],
        [mbx_list,   0],
        [pool_list,  0],
    ]

    micro_objs_h_data += generate_obj_id_lines(obj_types)


def generate_micro_objs_h_misc():

    global micro_objs_h_data
    micro_objs_h_data += "\n" + \
        "#define TICKFREQ 1000\n" + \
        "#define DATALEN 32768\n" + \
        "#define CEILING_PRIO 5\n" + \
        "#define KERNEL_PRIO 0\n" + \
        "#define DRIVER_PRIO 1\n" + \
        "#define TICKTIME 1000\n"


def micro_objs_h_generate():

    generate_micro_objs_h_header()
    generate_micro_objs_h_taskgroups()
    generate_micro_objs_h_nodes()
    generate_micro_objs_h_obj_ids()
    generate_micro_objs_h_misc()    # XXX - remove when ready
    generate_micro_objs_h_footer()

    write_file(output_dir + 'microkernel_objects.h', micro_objs_h_data)


vxmicro_h_filename_str = \
    "/* vxmicro.h - microkernel master header file */\n\n"

vxmicro_h_include_guard = "_VXMICRO__H_"

vxmicro_h_header_include_guard_str = \
    "#ifndef " + vxmicro_h_include_guard + "\n" \
    "#define " + vxmicro_h_include_guard + "\n\n"


def generate_vxmicro_h_header():

    global vxmicro_h_data
    vxmicro_h_data += \
        vxmicro_h_filename_str + \
        copyright + \
        do_not_edit_warning + \
        vxmicro_h_header_include_guard_str + \
        "#include <microkernel.h>\n" + \
        "#include <microkernel_objects.h>\n"


def generate_vxmicro_h_misc():

    global vxmicro_h_data
    vxmicro_h_data += "\n" + \
        "extern const int K_max_eventnr;\n" + \
        "extern struct evstr EVENTS[];\n\n"


def generate_vxmicro_h_obj_ids():

    global vxmicro_h_data

    base_event = 4  # events start at 4
    event_id = base_event
    for event in event_list:
        vxmicro_h_data += "#define %s %u\n" % (str(event[0]), event_id)
        event_id += 1
    if event_id > base_event:
        vxmicro_h_data += "\n"

    obj_types = [
        [map_list, 0],
    ]
    vxmicro_h_data += generate_obj_id_lines(obj_types)


vxmicro_h_footer_include_guard_str = \
    "\n#endif /* " + vxmicro_h_include_guard + " */\n"


def generate_vxmicro_h_task_entry_points():

    global vxmicro_h_data
    for task in task_list:
        vxmicro_h_data += "extern void %s(void);\n" % task[2]


def generate_vxmicro_h_footer():

    global vxmicro_h_data
    vxmicro_h_data += \
        vxmicro_h_footer_include_guard_str


def vxmicro_h_generate():
    """ Generate vxmicro.h file """

    generate_vxmicro_h_header()
    generate_vxmicro_h_misc()
    generate_vxmicro_h_obj_ids()
    generate_vxmicro_h_task_entry_points()
    generate_vxmicro_h_footer()

    write_file(output_dir + 'vxmicro.h', vxmicro_h_data)

# System generator mainline

vpf_parse()
kernel_main_c_generate()
vxmicro_h_generate()
micro_objs_h_generate()
