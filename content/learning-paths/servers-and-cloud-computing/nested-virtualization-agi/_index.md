---
title: Enable nested virtualization on an Arm AGI CPU host

draft: true
cascade:
    draft: true

description: Configure an Ubuntu 24.04 Arm AGI CPU host to run a KVM hypervisor VM, then create and verify a hardware-accelerated nested Ubuntu VM.
minutes_to_complete: 120
who_is_this_for: This Learning Path is for infrastructure developers and system administrators who want to run virtual machines inside virtual machines on an Arm AGI CPU host.
learning_objectives:
    - Enable and verify nested KVM support on an Ubuntu 24.04 Arm AGI CPU host.
    - Expose Arm virtualization extensions to an Ubuntu hypervisor VM.
    - Create an Ubuntu VM inside the hypervisor VM and verify that it uses KVM.
prerequisites:
    - A bare-metal Arm AGI CPU host running Ubuntu 24.04 Arm64, with firmware that exposes EL2 and FEAT_NV2 to Linux
    - A platform-supported host kernel with Arm64 nested KVM support; this path targets Linux 6.16 or later
    - At least 8 available CPU cores, 16 GB of available memory, and 100 GB of free storage
    - Root or sudo access, permission to reboot the host, and access to its recovery console
    - Outbound internet access from the host and VMs, and familiarity with Linux, SSH, and virtual machines

author: Pareena Verma

generate_summary_faq: true
rerun_summary: false
rerun_faqs: false

### Tags
skilllevels: Advanced
subjects: Containers and Virtualization
armips:
    - Neoverse
platforms:
    - Arm AGI CPU
tools_software_languages:
    - KVM
    - libvirt
    - virsh
    - virt-install
operatingsystems:
    - Linux

further_reading:
    - resource:
        title: Configure and run nested virtualization on an Arm server
        link: /learning-paths/servers-and-cloud-computing/nested-virtualization/
        type: learningpath
    - resource:
        title: Deploy Ceph RBD block storage on an Arm AGI CPU host
        link: /learning-paths/servers-and-cloud-computing/ceph-rbd-agi/
        type: learningpath
    - resource:
        title: Linux kernel command-line parameters
        link: https://www.kernel.org/doc/html/latest/admin-guide/kernel-parameters.html
        type: documentation
    - resource:
        title: QEMU Arm virt machine
        link: https://www.qemu.org/docs/master/system/arm/virt.html
        type: documentation
    - resource:
        title: Ubuntu kernel lifecycle and enablement stack
        link: https://ubuntu.com/kernel/lifecycle
        type: documentation

### FIXED, DO NOT MODIFY
# ================================================================================
weight: 1
layout: "learningpathall"
learning_path_main_page: "yes"
---
