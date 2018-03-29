#!/bin/bash
# Check the checkpoint directory and log directory, match with simpoint_fs_eembc.py
# Select the test array 
CONFIG=$1
#declare -a arr=("a2time01" "aifftr01" "aifirf01" "aiifft01" "basefp01" "bitmnp01" "cacheb01" "canrdr01" "idctrn01" "iirflt01" "matrix01" "pntrch01" "puwmod01" "rspeed01" "tblook01" "ttsprk01" "latency" "bwr")
#declare -a arr=("latency" "bwr")
# L1 MPKI > 1
#declare -a arr=("aifftr01" "aiifft01" "cacheb01" "matrix01")
#declare -a arr=("cjpeg" "djpeg" "rgbcmy01" "rgbhpg01" "rgbyiq01")
#declare -a arr=("cjpeg" "djpeg")
#declare -a arr=("rgbhpg01")
#Solo
#declare -a arr=("aifirf01" "pntrch01" "puwmod01" "cacheb01" "iirflt01" "aiifft01" "ttsprk01" "tblook01" "nmpc")
#declare -a arr=("aiifft01")
#1RT
#declare -a arr=("aifirf01-1RT" "pntrch01-1RT" "puwmod01-1RT" "cacheb01-1RT" "iirflt01-1RT" "aiifft01-1RT" "ttsprk01-1RT" "tblook01-1RT" "nmpc-1RT")
#2RT
#declare -a arr=("aifirf01-2RT" "pntrch01-2RT" "puwmod01-2RT" "cacheb01-2RT" "iirflt01-2RT" "aiifft01-2RT" "ttsprk01-2RT" "tblook01-2RT" "nmpc-2RT")
#3RT
#declare -a arr=("aifirf01-3RT" "pntrch01-3RT" "puwmod01-3RT" "cacheb01-3RT" "iirflt01-3RT" "aiifft01-3RT" "ttsprk01-3RT" "tblook01-3RT" "nmpc-3RT")

declare -a arr=("a2time01" "aifftr01" "aifirf01" "aiifft01" "basefp01" "bitmnp01" "cacheb01" "canrdr01" "idctrn01" "iirflt01" "matrix01" "pntrch01" "puwmod01" "rspeed01" "tblook01" "ttsprk01" "cjpeg" "djpeg" "rgbcmy01" "rgbhpg01" "rgbyiq01")
for i in "${arr[@]}"
do
     gnome-terminal -x bash -c "./build/ARM/gem5.opt -d RTAS-solo-L2-2MB --stats-file=${i}-${CONFIG}.txt  configs/spec2006/simpoint_fs_eembc.py --cfg=configs/spec2006/arm.cfg --disk-image=/home/prathap/WorkSpace/gem5/fullsystem/disks/linux-arm-ael.img --num-cpus=4 --mem-size=2048MB --kernel=/home/prathap/WorkSpace/linux-linaro-tracking-gem5/vmlinux --machine-type=VExpress_EMM --dtb-file=/home/prathap/WorkSpace/linux-linaro-tracking-gem5/arch/arm/boot/dts/vexpress-v2p-ca15-tc1-gem5_4cpus.dtb --mem-type=lpddr2_s4_1066_x32  --simpoint-mode=batch --benchmark=$i --checkpoint-dir=m5out-cache-part"&
done
           
     #gnome-terminal -x bash -c "./build/ARM/gem5.opt -d eembc-char1 --stats-file=${i}.txt --debug-flags=PK --debug-file=dump${i} configs/spec2006/simpoint_fs_eembc.py --cfg=configs/spec2006/arm.cfg --disk-image=/home/prathap/WorkSpace/gem5/fullsystem/disks/linux-arm-ael.img --num-cpus=4 --mem-size=2048MB --kernel=/home/prathap/WorkSpace/linux-linaro-tracking-gem5/vmlinux --machine-type=VExpress_EMM --dtb-file=/home/prathap/WorkSpace/linux-linaro-tracking-gem5/arch/arm/boot/dts/vexpress-v2p-ca15-tc1-gem5_4cpus.dtb --mem-type=lpddr2_s4_1066_x32  --simpoint-mode=batch --benchmark=$i --checkpoint-dir=m5out-1RT && sleep 8d"
#--debug-flags=PK --debug-file=dump${i}-${CONFIG}
#declare -a arr=("a2time01" "aifftr01" "aifirf01" "aiifft01" "basefp01" "bitmnp01" "cacheb01" "canrdr01" "idctrn01" "iirflt01" "matrix01" "pntrch01" "puwmod01" "rspeed01" "tblook01" "ttsprk01")
