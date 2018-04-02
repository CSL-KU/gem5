#!/bin/bash

declare -a arr=("3disparity-inf-1bzip2-ei-dmt98" "3mser-inf-1bzip2-ei-dmt98" "3sift-inf-1bzip2-ei-dmt98" "3svm-inf-1bzip2-ei-dmt98" "3texture_synthesis-inf-1bzip2-ei-dmt98" "3aifftr01-inf-1bzip2-ei-dmt98" "3aiifft01-inf-1bzip2-ei-dmt98" "3matrix01-inf-1bzip2-ei-dmt98" "3disparity-inf-1bzip2-ei-dmt90" "3mser-inf-1bzip2-ei-dmt90" "3sift-inf-1bzip2-ei-dmt90" "3svm-inf-1bzip2-ei-dmt90" "3texture_synthesis-inf-1bzip2-ei-dmt90" "3aifftr01-inf-1bzip2-ei-dmt90" "3aiifft01-inf-1bzip2-ei-dmt90" "3matrix01-inf-1bzip2-ei-dmt90" "3disparity-inf-1bzip2-ei-dma" "3mser-inf-1bzip2-ei-dma" "3sift-inf-1bzip2-ei-dma" "3svm-inf-1bzip2-ei-dma" "3texture_synthesis-inf-1bzip2-ei-dma" "3aifftr01-inf-1bzip2-ei-dma" "3aiifft01-inf-1bzip2-ei-dma" "3matrix01-inf-1bzip2-ei-dma" "3disparity-inf-1bzip2-ei-dmh" "3mser-inf-1bzip2-ei-dmh" "3sift-inf-1bzip2-ei-dmh" "3svm-inf-1bzip2-ei-dmh" "3texture_synthesis-inf-1bzip2-ei-dmh" "3aifftr01-inf-1bzip2-ei-dmh" "3aiifft01-inf-1bzip2-ei-dmh" "3matrix01-inf-1bzip2-ei-dmh" "3disparity-inf-1bzip2-ei-wp" "3mser-inf-1bzip2-ei-wp" "3sift-inf-1bzip2-ei-wp" "3svm-inf-1bzip2-ei-wp" "3texture_synthesis-inf-1bzip2-ei-wp" "3aifftr01-inf-1bzip2-ei-wp" "3aiifft01-inf-1bzip2-ei-wp" "3matrix01-inf-1bzip2-ei-wp" "3disparity-inf-1bzip2-ei-nop" "3mser-inf-1bzip2-ei-nop" "3sift-inf-1bzip2-ei-nop" "3svm-inf-1bzip2-ei-nop" "3texture_synthesis-inf-1bzip2-ei-nop" "3aifftr01-inf-1bzip2-ei-nop" "3aiifft01-inf-1bzip2-ei-nop" "3matrix01-inf-1bzip2-ei-nop")

disk_image_path=$(realpath ../full_system_images/disks/linux-arm-ael.img)
kernel_path=$(realpath ../gem5-linux/vmlinux)

for i in "${arr[@]}"
do
     gnome-terminal -x bash -c "./build/ARM/gem5.opt -d ../results/be-effect --stats-file=$i.txt configs/spec2006/simpoint_fs.py --cfg=configs/spec2006/arm.cfg --disk-image=${disk_image_path} --num-cpus=4 --mem-size=2048MB --kernel=${kernel_path} --machine-type=VExpress_EMM --mem-type=lpddr2_s4_1066_x32 --simpoint-mode=batch --benchmark=$i --checkpoint-dir=m5out/cpt.7846767145000"
done
