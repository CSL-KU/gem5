/*
 * Copyright (c) 2014 The Regents of The University of Michigan
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
 * Authors: Anthony Gutierrez
 */

/**
 * @file
 * Definitions of a random replacement tag store.
 */

#include "base/random.hh"
#include "debug/CacheRepl.hh"
#include "mem/cache/tags/random_repl.hh"
#include "mem/cache/base.hh"

RandomRepl::RandomRepl(const Params *p)
    : BaseSetAssoc(p)

{
}

BaseSetAssoc::BlkType*
RandomRepl::accessBlock(Addr addr, bool is_secure, Cycles &lat, int master_id, PacketPtr pkt)
{
    return BaseSetAssoc::accessBlock(addr, is_secure, lat, master_id, pkt);
}

BaseSetAssoc::BlkType*
RandomRepl::findVictim(Addr addr) const
{
    BlkType *blk = NULL;

    if (cache->getIsTopLevel() || cache->system->getWayPartMode() != 2) {
        blk = BaseSetAssoc::findVictim(addr);
        // if all blocks are valid, pick a replacement at random
        if (blk->isValid()) {
            int idx = random_mt.random<int>(lowerWayNum, upperWayNum);
            blk = sets[extractSet(addr)].blks[idx];
        }
    } 
    else {
        int set = extractSet(addr);
        // prefer to evict an invalid block
        for (int i = 0; i < assoc; ++i) {
            BlkType *b = sets[set].blks[i];
            if (!b->isValid() && ((dmAssoc && i >= lowerWayNum && i <= upperWayNum) || !dmAssoc)) {
                blk = b;
                break;
            }
        }
        // could not find an invalid block; looking into non-DM blocks to evict
        if (blk == NULL) {
            BlkType **available_blks = new BlkType*[assoc];
            int num_available_blks = 0;
            
            for (int i = 0; i < assoc; ++i) {
                BlkType *b = sets[set].blks[i];
                if (!b->isDeterministic() && ((dmAssoc && i >= lowerWayNum && i <= upperWayNum) || !dmAssoc)) {
                    available_blks[num_available_blks++] = b;
                }
            }
            if (num_available_blks != 0) {
                int idx = random_mt.random<int>(0, num_available_blks - 1);
                blk = available_blks[idx];
            }
            delete available_blks;
        }
        // could not find a non-DM block and the request is DM
        if (blk == NULL && dmAssoc) {
            int idx = random_mt.random<int>(lowerWayNum, upperWayNum);
            blk = sets[set].blks[idx];
        }
    }
    
    assert(blk != NULL);
    
    DPRINTF(CacheRepl, "set %x: selecting blk %x for replacement\n",
            blk->set, regenerateBlkAddr(blk->tag, blk->set));

    return blk;
}

void
RandomRepl::insertBlock(PacketPtr pkt, BlkType *blk)
{
    BaseSetAssoc::insertBlock(pkt, blk);
}

void
RandomRepl::invalidate(BlkType *blk)
{
    BaseSetAssoc::invalidate(blk);
}

RandomRepl*
RandomReplParams::create()
{
    return new RandomRepl(this);
}
