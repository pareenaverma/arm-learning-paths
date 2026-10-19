---
title: Verify nested KVM and run a workload
description: Confirm hardware acceleration at both VM layers, exercise the nested guest, and troubleshoot common failures.
weight: 5

### FIXED, DO NOT MODIFY
layout: learningpathall
---

## Confirm the full nesting chain

A successful L2 boot is useful, but you also need evidence that it is hardware accelerated. Keep the layer labels in mind: L0's libvirt manages L1, and L1's libvirt manages L2.

From **L2**, return to **L1**:

```bash
exit
```

On **L1**, ask the running L2 QEMU process whether it uses KVM:

```bash
sudo virsh --connect qemu:///system list --all
sudo virsh --connect qemu:///system qemu-monitor-command \
  agi-l2-guest --pretty '{"execute":"query-kvm"}'
```

The expected response contains:

```json
{
  "return": {
    "enabled": true,
    "present": true
  }
}
```

`enabled: true` verifies active KVM acceleration for L2. `present: true` alone only identifies a QEMU build with KVM support, as defined in the [QEMU QMP reference](https://www.qemu.org/docs/master/interop/qemu-qmp-ref.html#command-query-kvm).

Confirm that the running L2 definition contains the tested user-mode network and Arm virtio device:

```bash
sudo virsh --connect qemu:///system dumpxml agi-l2-guest \
  | sed -n '/<qemu:commandline>/,/<\/qemu:commandline>/p'
```

The expected section is:

```output
<qemu:commandline>
  <qemu:arg value='-netdev'/>
  <qemu:arg value='user,id=l2net,hostfwd=tcp:127.0.0.1:2222-:22'/>
  <qemu:arg value='-device'/>
  <qemu:arg value='virtio-net-device,netdev=l2net,mac=52:54:00:a6:02:01'/>
</qemu:commandline>
```

Open a separate terminal on **L0** and check L1 in the same way:

```bash
sudo virsh --connect qemu:///system qemu-monitor-command \
  agi-l1-hyper --pretty '{"execute":"query-kvm"}'
```

Both `enabled` and `present` must be `true`. Combined with the L0 nested-mode boot log, these checks demonstrate the chain from the AGI host through an L1 KVM hypervisor to an L2 KVM guest.

## Run a workload in L2

From your **L1** terminal, reconnect to **L2**:

```bash
ssh -i "${HOME}/.ssh/agi_nested_l2" -p 2222 ubuntu@127.0.0.1
```

Inside **L2**, install and run a short CPU workload:

```bash
sudo apt update
sudo apt install -y sysbench
sysbench cpu --threads=2 --time=10 run
```

The package installation also exercises L2's DNS and outbound connectivity through QEMU user-mode networking. Confirm that `sysbench` completes and reports CPU events and latency statistics. This is a functional smoke test, not an AGI performance result or an overhead comparison.

L2 does not need `/dev/kvm` for this workload. Its absence is expected when virtualization extensions are not exposed to L2.

## Record your validation results

For a repeatable validation record, capture these details:

| Layer | Evidence |
| --- | --- |
| L0 | AGI system and firmware identification, `uname -r`, `/proc/cmdline`, nested KVM boot messages, selected QEMU version, direct-boot file checksums, and L1 `query-kvm` response |
| L1 | `uname -r`, QEMU version, EL2/KVM boot messages, `/dev/kvm`, L2 domain XML, and L2 `query-kvm` response |
| L2 | Ubuntu version, `uname -r`, cloud-init status, successful workload output |

On **L0**, save the actual L1 definition and query the configured emulator path:

```bash
sudo virsh --connect qemu:///system dumpxml agi-l1-hyper > agi-l1-hyper.xml
sudo virsh --connect qemu:///system dumpxml agi-l1-hyper | grep '<emulator>'
sudo virsh --connect qemu:///system version
```

On **L1**, save the L2 definition:

```bash
sudo virsh --connect qemu:///system dumpxml agi-l2-guest > agi-l2-guest.xml
```

This records which binary libvirt actually used, rather than relying only on the default binary in your shell's search path.

## Troubleshoot by layer

| Symptom | Check and next action |
| --- | --- |
| L0 has `/dev/kvm` but no nested-mode initialization | Confirm the running kernel supports Arm64 nested KVM, the boot argument reached `/proc/cmdline`, and firmware exposes EL2 and FEAT_NV2. Ordinary KVM support is insufficient. |
| L0 still boots without nested mode | Confirm `kvm-arm.mode=nested` appears in `/proc/cmdline`, then inspect the bootloader configuration. The platform kernel already used in this path does not need replacement. |
| A libvirt NAT network fails with an `iptables` REJECT error | Do not create the NAT network on this AGI kernel. Use the `passt` configuration for L1 and QEMU user-mode networking for L2 from this Learning Path. |
| L1 fails to start with a virtualization or KVM capability error | Verify the emulator path in the L1 XML, confirm QEMU 11.1.2, and check the L0 nested-mode log. Confirm the QEMU machine option is present. |
| Libvirt rejects the custom emulator or reports permission denied | Inspect `sudo journalctl -u libvirtd -b` and kernel AppArmor denials on L0. Check executable and directory permissions under `/opt/qemu-11.1.2`. Use a platform-packaged QEMU or a narrowly scoped local policy adjustment if required; do not disable AppArmor globally. |
| L1 shows a synchronous UEFI exception or hangs at EL2 | Complete the initial UEFI boot with virtualization disabled, then use the direct-kernel configuration. Confirm ACPI is absent and SVE is disabled in the persistent L1 XML. |
| L1 boots but has no `/dev/kvm` | Check L1's EL2/KVM boot log and the L0 domain's `virtualization=on` setting. Shut down and restart L1 after changing its persistent XML; an in-guest reboot does not restart QEMU with new settings. |
| L2 fails with KVM errors | Inspect the L1 KVM boot log and `/var/log/libvirt/qemu/agi-l2-guest.log` inside L1. Verify KVM device access; do not switch to software emulation to bypass the failure. |
| L1 or L2 resets an SSH connection during first boot | Open the relevant serial console and wait for cloud-init to finish. Confirm the appropriate `passt` or QEMU process listens on `127.0.0.1:2222`. |
| L2 has no network | Confirm the L2 XML contains `user,id=l2net,hostfwd=tcp:127.0.0.1:2222-:22` and `virtio-net-device`. Confirm its MAC matches the cloud-init network configuration. |
| L2 cannot reach package repositories | Test name resolution with `getent hosts ports.ubuntu.com` inside L2 and inspect the L2 QEMU command line in the domain XML. |

To inspect L1 boot output, run on **L0**:

```bash
sudo virsh --connect qemu:///system console agi-l1-hyper
```

To inspect L2 boot output, run on **L1**:

```bash
sudo virsh --connect qemu:///system console agi-l2-guest
```

Press **Ctrl+]** to leave a console. These cloud images use SSH keys; no password was configured for console login.

## Shut down the lab

When finished, leave **L2** with `exit` and shut it down from **L1**:

```bash
sudo virsh --connect qemu:///system shutdown agi-l2-guest
sudo virsh --connect qemu:///system domstate agi-l2-guest
```

Wait until the state is `shut off`. Then leave L1 with `exit` and shut it down from **L0**:

```bash
sudo virsh --connect qemu:///system shutdown agi-l1-hyper
sudo virsh --connect qemu:///system domstate agi-l1-hyper
```

These commands retain the disks and definitions. To resume, start `agi-l1-hyper` from L0, reconnect to port 2222 over SSH, and start `agi-l2-guest` from L1. Both SSH forwards become available when their corresponding VM starts; the VMs do not autostart in this example.

If you want to return a GRUB-based L0 host to its previous KVM mode, first shut down the lab. Remove only the drop-in created by this path, regenerate GRUB configuration, and reboot:

```bash
sudo rm /etc/default/grub.d/99-agi-nested.cfg
sudo update-grub
sudo reboot
```

This does not remove VM data or uninstall the newer kernel or QEMU. L1 will require nested mode to be re-enabled before it can run as a hypervisor again.

## What you've accomplished

You've configured nested virtualization on an Ubuntu 24.04 AGI host, exposed EL2 to an L1 hypervisor, and verified that its L2 guest runs with KVM acceleration. You can now use the nested guest as a starting point for testing VM-based development or infrastructure workflows. For an overhead comparison, the original nested virtualization Learning Path provides a separate benchmarking exercise.
