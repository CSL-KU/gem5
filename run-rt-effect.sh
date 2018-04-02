#!/bin/bash

declare -a arr=("disparity-itr2-sim-3b683-dmt98-mdu" "mser-itr2-sim-3b683-dmt98-mdu" "sift-itr2-sim-3b683-dmt98-mdu" "svm-itr2-sim-3b683-dmt98-mdu" "texture_synthesis-itr2-sim-3b683-dmt98-mdu" "aifftr01-3b683-dmt98-mdu" "aiifft01-3b683-dmt98-mdu" "matrix01-3b683-dmt98-mdu" "disparity-itr2-sim-3b683-dmt90-mdu" "mser-itr2-sim-3b683-dmt90-mdu" "sift-itr2-sim-3b683-dmt90-mdu" "svm-itr2-sim-3b683-dmt90-mdu" "texture_synthesis-itr2-sim-3b683-dmt90-mdu" "aifftr01-3b683-dmt90-mdu" "aiifft01-3b683-dmt90-mdu" "matrix01-3b683-dmt90-mdu" "disparity-itr2-sim-3b683-dma-mdu" "mser-itr2-sim-3b683-dma-mdu" "sift-itr2-sim-3b683-dma-mdu" "svm-itr2-sim-3b683-dma-mdu" "texture_synthesis-itr2-sim-3b683-dma-mdu" "aifftr01-3b683-dma-mdu" "aiifft01-3b683-dma-mdu" "matrix01-3b683-dma-mdu" "disparity-itr2-sim-3b683-wp-mdu" "mser-itr2-sim-3b683-wp-mdu" "sift-itr2-sim-3b683-wp-mdu" "svm-itr2-sim-3b683-wp-mdu" "texture_synthesis-itr2-sim-3b683-wp-mdu" "aifftr01-3b683-wp-mdu" "aiifft01-3b683-wp-mdu" "matrix01-3b683-wp-mdu" "disparity-itr2-sim-3b683-solo-mdu" "mser-itr2-sim-3b683-solo-mdu" "sift-itr2-sim-3b683-solo-mdu" "svm-itr2-sim-3b683-solo-mdu" "texture_synthesis-itr2-sim-3b683-solo-mdu" "aifftr01-3b683-solo-mdu" "aiifft01-3b683-solo-mdu" "matrix01-3b683-solo-mdu" "disparity-itr2-sim-3b683-nop-mdu" "mser-itr2-sim-3b683-nop-mdu" "sift-itr2-sim-3b683-nop-mdu" "svm-itr2-sim-3b683-nop-mdu" "texture_synthesis-itr2-sim-3b683-nop-mdu" "aifftr01-3b683-nop-mdu" "aiifft01-3b683-nop-mdu" "matrix01-3b683-nop-mdu")

disk_image_path=$(realpath ../full_system_images/disks/linux-arm-ael.img)
kernel_path=$(realpath ../gem5-linux/vmlinux)

for i in "${arr[@]}"
do
     gnome-terminal -x bash -c "./build/ARM/gem5.opt -d ../results/rt-effect --stats-file=$i.txt configs/spec2006/simpoint_fs.py --cfg=configs/spec2006/arm.cfg --disk-image=${disk_image_path} --num-cpus=4 --mem-size=2048MB --kernel=${kernel_path} --machine-type=VExpress_EMM --mem-type=lpddr2_s4_1066_x32 --simpoint-mode=batch --benchmark=$i --checkpoint-dir=m5out/cpt.7846767145000"
done
