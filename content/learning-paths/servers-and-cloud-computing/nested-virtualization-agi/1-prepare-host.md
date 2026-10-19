---
title: Prepare the Ubuntu 24.04 AGI host
description: Check the host kernel and QEMU, enable nested KVM, and prepare user-space networking.
weight: 2

### FIXED, DO NOT MODIFY
layout: learningpathall
---

## Run a hypervisor inside a VM

Nested virtualization lets you give a VM its own KVM hypervisor. This is useful for testing infrastructure or running VM-based development environments inside an isolated guest. In this Learning Path, you enable nested virtualization on a physical Arm AGI CPU host, start a hypervisor VM, and run a second VM inside it.

The layers are:

| Layer | System | Operating system | Resources |
| --- | --- | --- | --- |
| L0 | Physical AGI host | Ubuntu 24.04 Arm64 | Hosts L1 |
| L1 | `agi-l1-hyper` | Ubuntu 24.04 Arm64 | 8 vCPUs, 12 GiB RAM, 80 GiB disk |
| L2 | `agi-l2-guest`, inside L1 | Ubuntu 24.04 Arm64 | 2 vCPUs, 2 GiB RAM, 20 GiB disk |

L2 resources come from L1's allocation. Its disk is stored inside L1's disk. Run commands in Bash on the layer identified in each section. All `sudo virsh` commands use the system libvirt instance explicitly.

## Check the host kernel

Run these commands on **L0**:

```bash
uname -m
uname -r
```

The output from the AGI CPU host is similar to:

```output
aarch64
7.1.3-arm-agi-20260806-v0.6.2-gc21d8d94ca47
```

`aarch64` confirms the Arm64 architecture. The second line identifies the platform-specific AGI kernel running on this host; your kernel version can differ. This version output alone does not confirm that nested virtualization is enabled.

Check the Ubuntu release and virtualization boot messages:

```bash
cat /etc/os-release
sudo dmesg | grep -iE 'kvm|EL2|Nested Virtualization'
```

Before enabling nested mode, the filtered `dmesg` output can look like this AGI host example:

```output
[    0.000000] CPU features: detected: HCRX_EL2 register
[    0.124016] CPU: All CPU(s) started at EL2
[    0.374843] kvm [1]: nv: 570 coarse grained trap handlers
[    0.374949] kvm [1]: nv: 710 fine grained trap handlers
[    0.375011] kvm [1]: IPA Size Limit: 48 bits
[    0.381979] kvm [1]: GICv4 support disabled
[    0.381981] kvm [1]: GICv3: no GICV resource entry
[    0.381983] kvm [1]: disabling GICv2 emulation
[    0.390489] kvm [1]: GIC system register CPU interface enabled
[    0.390494] kvm [1]: vgic interrupt IRQ9
[    0.407509] kvm [1]: VHE mode initialized successfully
```

`All CPU(s) started at EL2` confirms that Linux started with access to EL2. `VHE mode initialized successfully` confirms ordinary KVM initialization in VHE mode. The `nv:` trap-handler lines alone do not confirm that nested virtualization is enabled. After enabling nested mode and rebooting later in this section, check for `VHE+NV2` initialization. Timestamps and trap-handler counts can vary by kernel and system.

Confirm `aarch64` and Ubuntu 24.04. The host needs firmware that exposes EL2 and hardware support for FEAT_NV2. A working `/dev/kvm` alone proves only ordinary virtualization.

Ubuntu 24.04's original 6.8 kernel is not sufficient for this workflow. This path targets a platform-supported Linux 6.16 or later kernel with Arm64 nested KVM enabled. Version numbers alone do not prove support; the boot checks below are mandatory. Earlier kernels or vendor backports need separate validation.

The example AGI host already runs a platform-specific 7.1.3 kernel, which exceeds this version baseline. Keep that kernel and continue to install the virtualization tools and enable nested mode below. Confirm nested support with the post-reboot checks before proceeding to L1 creation.

## Install the virtualization tools

On **L0**, install the virtualization tools:

```bash
sudo apt update
sudo apt install -y qemu-kvm qemu-utils qemu-efi-aarch64 \
  libvirt-daemon-system libvirt-clients libvirt-daemon-config-network \
  virtinst cloud-image-utils curl
sudo systemctl enable --now libvirtd
qemu-system-aarch64 --version
```

The example AGI host reports the following distribution-provided QEMU version:

```output
QEMU emulator version 8.2.2 (Debian 1:8.2.2+ds-0ubuntu1.18)
Copyright (c) 2003-2023 Fabrice Bellard and the QEMU Project developers
```

The L0 QEMU must be **10.1 or later**: [QEMU 10.1 introduced nested KVM support for the Arm virt machine](https://www.qemu.org/2025/08/26/qemu-10-1-0/). Installing Ubuntu 24.04's original QEMU packages does not meet that requirement. Use an updated platform package if available, or build a separate QEMU as shown below.

### Build a newer QEMU if needed

Skip this subsection if the packaged QEMU already meets the requirement. This example builds QEMU 11.1.2 from the [QEMU download site](https://www.qemu.org/download/) and installs it separately, leaving the distribution binary available for existing VMs. This locally built QEMU needs manual maintenance.

Run on **L0**:

```bash
sudo apt install -y build-essential ninja-build pkg-config python3-venv \
  libglib2.0-dev libpixman-1-dev zlib1g-dev libfdt-dev
(
set -e
mkdir -p "${HOME}/src/agi-nested"
cd "${HOME}/src/agi-nested"
curl --fail --location https://download.qemu.org/qemu-11.1.2.tar.xz \
  --output qemu-11.1.2.tar.xz
tar -xf qemu-11.1.2.tar.xz
cd qemu-11.1.2
./configure --prefix=/opt/qemu-11.1.2 --target-list=aarch64-softmmu \
  --enable-kvm --disable-docs
make -j8
sudo make install
)
/opt/qemu-11.1.2/bin/qemu-system-aarch64 --version
```

The output from the example AGI host after building QEMU is:

```output
QEMU emulator version 11.1.2
Copyright (c) 2003-2026 Fabrice Bellard and the QEMU Project developers
```

The L1 creation command on the next page explicitly selects this binary when used. Installing a newer QEMU does not automatically make libvirt select it.

## Enable nested KVM at boot

The [Linux kernel parameter documentation](https://www.kernel.org/doc/html/latest/admin-guide/kernel-parameters.html) defines `kvm-arm.mode=nested` for FEAT_NV2 hardware. This is a **host kernel argument**, separate from the QEMU machine option you will set for L1.

On an **L0 host that boots with GRUB**, first inspect existing settings:

```bash
cat /proc/cmdline
grep -R 'kvm-arm.mode' /etc/default/grub /etc/default/grub.d/ 2>/dev/null
```

Resolve any existing `kvm-arm.mode=protected`, `nvhe`, or `none` setting before adding the nested setting. Do not leave conflicting mode arguments. Create a GRUB drop-in:

```bash
sudo tee /etc/default/grub.d/99-agi-nested.cfg >/dev/null <<'EOF'
GRUB_CMDLINE_LINUX="${GRUB_CMDLINE_LINUX} kvm-arm.mode=nested"
EOF
sudo update-grub
sudo reboot
```

This reboots the physical host and interrupts its VMs. For a host that uses another bootloader, add the same kernel argument through that platform's boot configuration instead; the GRUB commands do not apply.

Reconnect to **L0** after reboot and check the running kernel and nested mode:

```bash
uname -r
cat /proc/cmdline
```

The example AGI host reports the following after reboot. The root UUID is specific to this host:

```output
7.1.3-arm-agi-20260806-v0.6.2-gc21d8d94ca47
BOOT_IMAGE=/vmlinuz-7.1.3-arm-agi-20260806-v0.6.2-gc21d8d94ca47 root=UUID=c585fc7f-658d-444a-93a3-4fc0e7b9ed85 ro kvm-arm.mode=nested console=tty1 console=ttyAMA0
```

Check the KVM initialization messages:

```bash
sudo dmesg | grep -iE 'Nested Virtualization|VHE|kvm'
```

The relevant initialization lines from the example AGI host are shown below. The matching kernel command-line entry is omitted:

```output
[    0.123902] CPU features: detected: Nested Virtualization Support
[    0.374915] kvm [1]: nv: 570 coarse grained trap handlers
[    0.375017] kvm [1]: nv: 710 fine grained trap handlers
[    0.375084] kvm [1]: IPA Size Limit: 48 bits
[    0.382302] kvm [1]: GICv4 support disabled
[    0.382304] kvm [1]: GICv3: no GICV resource entry
[    0.382305] kvm [1]: disabling GICv2 emulation
[    0.390810] kvm [1]: GIC system register CPU interface enabled
[    0.390816] kvm [1]: vgic interrupt IRQ9
[    0.407829] kvm [1]: VHE+NV2 mode initialized successfully
```

Confirm the intended kernel booted and `/proc/cmdline` contains `kvm-arm.mode=nested`. The kernel log should report nested support and initialization in `VHE+NV2` mode. Exact log text can vary by kernel. A message reporting only `VHE mode initialized successfully` is not sufficient. Stop here if nested initialization fails; check the kernel, firmware, and FEAT_NV2 support before creating L1.

Check the KVM device:

```bash
ls -l /dev/kvm
```

The output from the example AGI host is:

```output
crw-rw---- 1 root kvm 10, 232 Oct 14 18:10 /dev/kvm
```

Validate the host's virtualization devices and configuration:

```bash
sudo virt-host-validate qemu
```

The output from the example AGI host is:

```output
  QEMU: Checking if device /dev/kvm exists                                   : PASS
  QEMU: Checking if device /dev/kvm is accessible                            : PASS
  QEMU: Checking if device /dev/vhost-net exists                             : WARN (Load the 'vhost_net' module to improve performance of virtio networking)
  QEMU: Checking if device /dev/net/tun exists                               : PASS
  QEMU: Checking for cgroup 'cpu' controller support                         : PASS
  QEMU: Checking for cgroup 'cpuacct' controller support                     : PASS
  QEMU: Checking for cgroup 'cpuset' controller support                      : PASS
  QEMU: Checking for cgroup 'memory' controller support                      : PASS
  QEMU: Checking for cgroup 'devices' controller support                     : PASS
  QEMU: Checking for cgroup 'blkio' controller support                       : PASS
  QEMU: Checking for device assignment IOMMU support                         : PASS
  QEMU: Checking if IOMMU is enabled by kernel                               : PASS
  QEMU: Checking for secure guest support                                    : WARN (Unknown if this platform has Secure Guest support)
```

The KVM device checks must pass. You can ignore the `secure-guest` and `vhost_net`  warnings as these features are not used in this example.

## Install passt for L1 networking

This example uses `passt` for networking between L0 and L1. `passt` is a user-space networking service that connects virtual machines to the host network without requiring a Linux bridge or TAP device. It also forwards SSH connections from TCP port `2222` on L0 to port `22` on L1.

Install `passt` on **L0**:

```bash
sudo apt update
sudo apt install -y passt
command -v passt
dpkg-query -W -f='${Package} ${Version} ${Status}\n' passt
```

The output from the tested host is similar to:

```output
/usr/bin/passt
passt 0.0~git20240220.1e6f92b-1 install ok installed
```

Check that TCP port `2222` is available on L0. This port will forward SSH connections to L1:

```bash
sudo ss -ltnp 'sport = :2222'
```

An output table with no listener entry confirms that the port is available.

## What you've accomplished and what's next

You've prepared the Ubuntu tools, installed a QEMU version that supports nested KVM, verified `VHE+NV2` mode, and installed user-space networking for L1. Next, you'll create an Ubuntu L1 VM and expose virtual EL2 to it.
