/*
 * Copyright (c) 2013 ARM Limited
 * All rights reserved.
 *
 * The license below extends only to copyright in the software and shall
 * not be construed as granting a license to any other intellectual
 * property including but not limited to intellectual property relating
 * to a hardware implementation of the functionality of the software
 * licensed hereunder.  You may use the software subject to the license
 * terms below provided that you ensure that this notice is replicated
 * unmodified and in its entirety in all distributions of the software,
 * modified or unmodified, in source code or in binary form.
 *
 * Copyright (c) 2003-2005 The Regents of The University of Michigan
 * All rights reserved.
 *
 * Redistribution and use in source and binary forms, with or without
 * modification, are permitted provided that the following conditions are
 * met: redistributions of source code must retain the above copyright
 * notice, this list of conditions and the following disclaimer;
 * redistributions in binary form must reproduce the above copyright
 * notice, this list of conditions and the following disclaimer in the
 * documentation and/or other materials provided with the distribution;
 * neither the name of the copyright holders nor the names of its
 * contributors may be used to endorse or promote products derived from
 * this software without specific prior written permission.
 *
 * THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDERS AND CONTRIBUTORS
 * "AS IS" AND ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT
 * LIMITED TO, THE IMPLIED WARRANTIES OF MERCHANTABILITY AND FITNESS FOR
 * A PARTICULAR PURPOSE ARE DISCLAIMED. IN NO EVENT SHALL THE COPYRIGHT
 * OWNER OR CONTRIBUTORS BE LIABLE FOR ANY DIRECT, INDIRECT, INCIDENTAL,
 * SPECIAL, EXEMPLARY, OR CONSEQUENTIAL DAMAGES (INCLUDING, BUT NOT
 * LIMITED TO, PROCUREMENT OF SUBSTITUTE GOODS OR SERVICES; LOSS OF USE,
 * DATA, OR PROFITS; OR BUSINESS INTERRUPTION) HOWEVER CAUSED AND ON ANY
 * THEORY OF LIABILITY, WHETHER IN CONTRACT, STRICT LIABILITY, OR TORT
 * (INCLUDING NEGLIGENCE OR OTHERWISE) ARISING IN ANY WAY OUT OF THE USE
 * OF THIS SOFTWARE, EVEN IF ADVISED OF THE POSSIBILITY OF SUCH DAMAGE.
 *
 * Authors: Erik Hallnor
 *          Ron Dreslinski
 */

/**
 * @file
 * Definitions of BaseTags.
 */

#include "config/the_isa.hh"
#include "cpu/smt.hh" //maxThreadsPerCPU
#include "mem/cache/tags/base.hh"
#include "mem/cache/base.hh"
#include "sim/sim_exit.hh"

using namespace std;

BaseTags::BaseTags(const Params *p)
    : ClockedObject(p), blkSize(p->block_size), size(p->size),
      hitLatency(p->hit_latency), cache(nullptr), warmupBound(0),
      warmedUp(false), numBlocks(0)
{
}

void
BaseTags::setCache(BaseCache *_cache)
{
    assert(!cache);
    cache = _cache;
}

void
BaseTags::regStats()
{
    using namespace Stats;
    replacements
        .init(maxThreadsPerCPU)
        .name(name() + ".replacements")
        .desc("number of replacements")
        .flags(total)
        ;


    assert(cache->system->maxMasters() <= MAX_NUM_MASTER);
    
    for (int j = 0; j < cache->system->maxMasters(); j++)
    {  
	replacements_detail[j]
	    .init(cache->system->maxMasters())
	    .name(name() + "." + cache->system->getMasterName(j) + "_replaced")
	    .desc("Number of replacements for the blocks allocated by " + cache->system->getMasterName(j))
	    .flags(total | nozero | nonan)
	    ;
	for (int i = 0; i < cache->system->maxMasters(); i++) {
	    replacements_detail[j].subname(i, cache->system->getMasterName(i));
	}
    }
    for (int j = cache->system->maxMasters(); j < MAX_NUM_MASTER; j++)
    {
        string j_str = to_string(j);

        replacements_detail[j]
            .init(1)
            .name(name() + ".replacements_detail_dummy" + j_str)
            .desc("dummy")
            .flags(total | nozero | nonan)
            ;
    }

    determ_replacements
        .init(cache->system->maxMasters())
        .name(name() + ".determ_replacements")
        .desc("Number of deterministic blocks replacements by this master")
        .flags(total | nozero | nonan)
        ;
    for (int i = 0; i < cache->system->maxMasters(); i++) {
        determ_replacements.subname(i, cache->system->getMasterName(i));
    }

    determ_blks
        .init(cache->system->maxMasters())
        .name(name() + ".determ_blks")
        .desc("Number of allocated deterministic blocks from last stat reset")
        .flags(total | nozero | nonan)
        ;
    for (int i = 0; i < cache->system->maxMasters(); i++) {
        determ_blks.subname(i, cache->system->getMasterName(i));
    }

    avg_determ_blks
        .init(cache->system->maxMasters())
        .name(name() + ".avg_determ_blks")
        .desc("Average number of deterministic blocks")
        .flags(total | nozero | nonan)
        ;
    for (int i = 0; i < cache->system->maxMasters(); i++) {
        avg_determ_blks.subname(i, cache->system->getMasterName(i));
    }

    tagsInUse
        .name(name() + ".tagsinuse")
        .desc("Cycle average of tags in use")
        ;

    totalRefs
        .name(name() + ".total_refs")
        .desc("Total number of references to valid blocks.")
        ;

    sampledRefs
        .name(name() + ".sampled_refs")
        .desc("Sample count of references to valid blocks.")
        ;

    avgRefs
        .name(name() + ".avg_refs")
        .desc("Average number of references to valid blocks.")
        ;

    avgRefs = totalRefs/sampledRefs;

    warmupCycle
        .name(name() + ".warmup_cycle")
        .desc("Cycle when the warmup percentage was hit.")
        ;

    occupancies
        .init(cache->system->maxMasters())
        .name(name() + ".occ_blocks")
        .desc("Average occupied blocks per requestor")
        .flags(nozero | nonan)
        ;
    for (int i = 0; i < cache->system->maxMasters(); i++) {
        occupancies.subname(i, cache->system->getMasterName(i));
    }

    avgOccs
        .name(name() + ".occ_percent")
        .desc("Average percentage of cache occupancy")
        .flags(nozero | total)
        ;
    for (int i = 0; i < cache->system->maxMasters(); i++) {
        avgOccs.subname(i, cache->system->getMasterName(i));
    }

    avgOccs = occupancies / Stats::constant(numBlocks);

    occupanciesReset
        .init(cache->system->maxMasters())
        .name(name() + ".occ_blocks_reset")
        .desc("Occupied blocks per requestor requested after the stat reset")
        .flags(nozero | nonan)
        ;
    for (int i = 0; i < cache->system->maxMasters(); i++) {
        occupanciesReset.subname(i, cache->system->getMasterName(i));
    }

    occsReset
        .name(name() + ".occ_percent_reset")
        .desc("Percentage of cache occupancy requested after the stat reset")
        .flags(nozero | total)
        ;
    for (int i = 0; i < cache->system->maxMasters(); i++) {
        occsReset.subname(i, cache->system->getMasterName(i));
    }

    occsReset = occupanciesReset / Stats::constant(numBlocks);
    
    occupanciesTaskId
        .init(ContextSwitchTaskId::NumTaskId)
        .name(name() + ".occ_task_id_blocks")
        .desc("Occupied blocks per task id")
        .flags(nozero | nonan)
        ;

    ageTaskId
        .init(ContextSwitchTaskId::NumTaskId, 5)
        .name(name() + ".age_task_id_blocks")
        .desc("Occupied blocks per task id")
        .flags(nozero | nonan)
        ;

    percentOccsTaskId
        .name(name() + ".occ_task_id_percent")
        .desc("Percentage of cache occupancy per task id")
        .flags(nozero)
        ;

    percentOccsTaskId = occupanciesTaskId / Stats::constant(numBlocks);

    tagAccesses
        .name(name() + ".tag_accesses")
        .desc("Number of tag accesses")
        ;

    dataAccesses
        .name(name() + ".data_accesses")
        .desc("Number of data accesses")
        ;

    registerDumpCallback(new BaseTagsDumpCallback(this));
    registerExitCallback(new BaseTagsCallback(this));
}
