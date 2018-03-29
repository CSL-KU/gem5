#!/bin/bash
# Check the checkpoint directory and log directory, match with simpoint_fs_eembc.py
# Select the test array 
CONFIG=$1
#isolbench
declare -a arr=("latency" "bwr")
#declare -a arr=("l-D1bwr" "l-D1bww" "bwr-D1bwr" "bwr-L1bwr" "bwr-D1bww" "bwr-L1bww" "l-D2bwr" "l-D2bww" "bwr-D2bwr" "bwr-L2bwr" "bwr-D2bww" "bwr-L2bww" "l-D3bwr" "l-D3bww" "bwr-D3bwr" "bwr-L3bwr" "bwr-D3bww" "bwr-L3bww")
for i in "${arr[@]}"
do
     gnome-terminal -x bash -c "./build/ARM/gem5.opt -d isolbench-agressive --stats-file=${i}-${CONFIG}.txt  configs/spec2006/simpoint_fs.py --cfg=configs/spec2006/arm.cfg --disk-image=/home/farshchi/projects/gem5/full_system_images/disks/linux-arm-ael.img --num-cpus=4 --mem-size=2048MB --kernel=/home/farshchi/projects/gem5/gem5-linux/vmlinux --machine-type=VExpress_EMM --dtb-file=/home/farshchi/projects/gem5/gem5-linux/arch/arm/boot/dts/vexpress-v2p-ca15-tc1-gem5_4cpus.dtb --mem-type=lpddr2_s4_1066_x32  --simpoint-mode=batch --benchmark=$i --checkpoint-dir=m5out && sleep 8d"&
done
           
     #gnome-terminal -x bash -c "./build/ARM/gem5.opt -d eembc-char1 --stats-file=${i}.txt --debug-flags=PK --debug-file=dump${i} configs/spec2006/simpoint_fs_eembc.py --cfg=configs/spec2006/arm.cfg --disk-image=/home/prathap/WorkSpace/gem5/fullsystem/disks/linux-arm-ael.img --num-cpus=4 --mem-size=2048MB --kernel=/home/prathap/WorkSpace/linux-linaro-tracking-gem5/vmlinux --machine-type=VExpress_EMM --dtb-file=/home/prathap/WorkSpace/linux-linaro-tracking-gem5/arch/arm/boot/dts/vexpress-v2p-ca15-tc1-gem5_4cpus.dtb --mem-type=lpddr2_s4_1066_x32  --simpoint-mode=batch --benchmark=$i --checkpoint-dir=m5out-1RT && sleep 8d"
#--debug-flags=PK --debug-file=dump${i}-${CONFIG}
#declare -a arr=("a2time01" "aifftr01" "aifirf01" "aiifft01" "basefp01" "bitmnp01" "cacheb01" "canrdr01" "idctrn01" "iirflt01" "matrix01" "pntrch01" "puwmod01" "rspeed01" "tblook01" "ttsprk01")
