#!/bin/bash

export M5_PATH=$(realpath ../full_system_images)
disk_image_path=$(realpath ../full_system_images/disks/linux-arm-ael.img)
kernel_path=$(realpath ../gem5-linux/vmlinux)
dtb_path=$(realpath ../gem5-linux/arch/arm/boot/dts/vexpress-v2p-ca15-tc1-gem5_4cpus.dtb)

rm -rf m5out
./build/ARM/gem5.opt -d m5out configs/example/fs.py --disk-image=${disk_image_path} --num-cpus=4 --caches --l2cache --mem-size=2048MB --kernel=${kernel_path} --machine-type=VExpress_EMM --dtb-file=${dtb_path} --mem-type=lpddr2_s4_1066_x32 --checkpoint-at-end