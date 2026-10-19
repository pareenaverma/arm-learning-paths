---
title: Create the L1 hypervisor VM
description: Create an Ubuntu 24.04 Arm64 VM and expose virtualization extensions so it can run KVM.
weight: 3

### FIXED, DO NOT MODIFY
layout: learningpathall
---

## Prepare the L1 image and SSH access

Run all commands in this section on **L0**. The L1 VM uses an Ubuntu 24.04 cloud image, a dedicated disk, and a cloud-init seed ISO. Keep the seed attached for subsequent boots.

Create a dedicated SSH key, preserving it if it already exists:

```bash
mkdir -p "${HOME}/.ssh"
chmod 700 "${HOME}/.ssh"
if [ ! -f "${HOME}/.ssh/agi_nested" ]; then
  ssh-keygen -t ed25519 -f "${HOME}/.ssh/agi_nested" -N ""
fi
```

Download a fresh image into this lab's directory. Run this once; do not overwrite an existing lab's disks:

```bash
(
set -e
VM_DIRECTORY=/var/lib/libvirt/images/agi-nested
sudo mkdir -p "$VM_DIRECTORY"
test ! -e "${VM_DIRECTORY}/ubuntu-24.04-arm64.img"
sudo curl --fail --location \
  https://cloud-images.ubuntu.com/releases/noble/release/ubuntu-24.04-server-cloudimg-arm64.img \
  --output "${VM_DIRECTORY}/ubuntu-24.04-arm64.img"
sudo qemu-img info "${VM_DIRECTORY}/ubuntu-24.04-arm64.img"
)
```

Confirm that the downloaded image is QCOW2. The release image changes over time; record its checksum when validating this path:

```bash
sudo sha256sum /var/lib/libvirt/images/agi-nested/ubuntu-24.04-arm64.img
```

## Create the disk and cloud-init seed

On **L0**, create an independent 80 GiB L1 disk. Cloud-init creates the `ubuntu` user and configures DHCP by MAC address:

```bash
(
set -e
VM_DIRECTORY=/var/lib/libvirt/images/agi-nested
SSH_PUBLIC_KEY="$(cat "${HOME}/.ssh/agi_nested.pub")"
SEED_DIRECTORY=$(mktemp -d)
test ! -e "${VM_DIRECTORY}/agi-l1-hyper.qcow2"
test ! -e "${VM_DIRECTORY}/agi-l1-hyper-seed.iso"
sudo qemu-img convert -f qcow2 -O qcow2 \
  "${VM_DIRECTORY}/ubuntu-24.04-arm64.img" "${VM_DIRECTORY}/agi-l1-hyper.qcow2"
sudo qemu-img resize "${VM_DIRECTORY}/agi-l1-hyper.qcow2" 80G
cat > "${SEED_DIRECTORY}/user-data" <<EOF
#cloud-config
hostname: agi-l1-hyper
manage_etc_hosts: true
ssh_pwauth: false
users:
  - name: ubuntu
    groups: [adm, sudo]
    shell: /bin/bash
    sudo: ALL=(ALL) NOPASSWD:ALL
    lock_passwd: true
    ssh_authorized_keys:
      - ${SSH_PUBLIC_KEY}
EOF
cat > "${SEED_DIRECTORY}/meta-data" <<'EOF'
instance-id: agi-l1-hyper
local-hostname: agi-l1-hyper
EOF
cat > "${SEED_DIRECTORY}/network-config" <<'EOF'
version: 2
ethernets:
  nestednic:
    match:
      macaddress: "52:54:00:a6:01:01"
    dhcp4: true
EOF
sudo cloud-localds --network-config="${SEED_DIRECTORY}/network-config" \
  "${VM_DIRECTORY}/agi-l1-hyper-seed.iso" \
  "${SEED_DIRECTORY}/user-data" "${SEED_DIRECTORY}/meta-data"
rm -r "$SEED_DIRECTORY"
)
```

## Boot L1 once without virtual EL2

The tested Ubuntu UEFI firmware raises a synchronous exception when L1 starts with virtual EL2 exposed. Boot L1 once without virtual EL2 so you can obtain the kernel and initramfs from the installed cloud image. You will then configure direct Linux kernel boot, bypassing UEFI for subsequent starts.

On **L0**, set the path to the QEMU 11.1.2 binary built on the previous page:

```bash
QEMU_BINARY=/opt/qemu-11.1.2/bin/qemu-system-aarch64
"$QEMU_BINARY" --version
```

Generate the initial domain XML without starting the VM:

```bash
sudo virt-install \
  --connect qemu:///system \
  --name agi-l1-hyper \
  --virt-type kvm \
  --arch aarch64 \
  --machine virt \
  --cpu host-passthrough \
  --vcpus 8 \
  --memory 12288 \
  --import \
  --osinfo generic \
  --boot "uefi,emulator=${QEMU_BINARY}" \
  --disk path=/var/lib/libvirt/images/agi-nested/agi-l1-hyper.qcow2,format=qcow2,bus=virtio \
  --disk path=/var/lib/libvirt/images/agi-nested/agi-l1-hyper-seed.iso,device=cdrom,format=raw \
  --network none \
  --qemu-commandline='-machine virtualization=off' \
  --graphics none \
  --noautoconsole \
  --print-xml > "${HOME}/agi-l1-hyper.xml"
```

Add a `passt` interface and forward L0 port `2222` to L1 port `22`:

```bash
python3 - <<'PY'
from pathlib import Path
import xml.etree.ElementTree as ET

path = Path.home() / "agi-l1-hyper.xml"
qemu_ns = "http://libvirt.org/schemas/domain/qemu/1.0"
ET.register_namespace("qemu", qemu_ns)

tree = ET.parse(path)
devices = tree.getroot().find("devices")
if devices is None:
    raise SystemExit("The domain XML has no devices element")

interface = ET.fromstring("""
<interface type='user'>
  <mac address='52:54:00:a6:01:01'/>
  <model type='virtio'/>
  <backend type='passt'/>
  <portForward proto='tcp' address='127.0.0.1'>
    <range start='2222' to='22'/>
  </portForward>
</interface>
""")
devices.append(interface)
ET.indent(tree, space="  ")
tree.write(path, encoding="unicode")
PY
```

Define and start the initial L1 configuration:

```bash
sudo virsh --connect qemu:///system define "${HOME}/agi-l1-hyper.xml"
sudo virsh --connect qemu:///system start agi-l1-hyper
sudo ss -ltnp 'sport = :2222'
```

Confirm that `passt` listens on `127.0.0.1:2222`. Connect from **L0** and wait for cloud-init:

```bash
ssh -i "${HOME}/.ssh/agi_nested" -p 2222 ubuntu@127.0.0.1
sudo cloud-init status --wait
```

The expected cloud-init status is `done`. Because virtual EL2 is disabled for this initial boot, `/dev/kvm` is not expected inside L1 yet.

## Copy the L1 kernel and initramfs to L0

Exit to **L0**:

```bash
exit
```

Record L1's kernel version and root filesystem UUID:

```bash
L1_KERNEL=$(ssh -T -i "${HOME}/.ssh/agi_nested" -p 2222 \
  ubuntu@127.0.0.1 'uname -r')
L1_ROOT_UUID=$(ssh -T -i "${HOME}/.ssh/agi_nested" -p 2222 \
  ubuntu@127.0.0.1 'findmnt -no UUID /')
printf 'Kernel: %s\nRoot UUID: %s\n' "$L1_KERNEL" "$L1_ROOT_UUID"
```

The tested image reported:

```output
Kernel: 6.8.0-142-generic
Root UUID: 86f7cf19-9959-4dba-91b1-0052c9d45c21
```

Your image can contain a newer Ubuntu 24.04 kernel and a different filesystem UUID. Copy its matching kernel and initramfs to L0:

```bash
(
set -e
BOOT_DIRECTORY=/var/lib/libvirt/images/agi-nested/direct-boot
sudo mkdir -p "$BOOT_DIRECTORY"

for FILE in "vmlinuz-${L1_KERNEL}" "initrd.img-${L1_KERNEL}"; do
  ssh -T -i "${HOME}/.ssh/agi_nested" -p 2222 \
    ubuntu@127.0.0.1 "sudo cat /boot/${FILE}" \
    | sudo tee "${BOOT_DIRECTORY}/${FILE}" >/dev/null
done
)
```

Compare the source and copied checksums:

```bash
ssh -T -i "${HOME}/.ssh/agi_nested" -p 2222 \
  ubuntu@127.0.0.1 \
  "sudo sha256sum /boot/vmlinuz-${L1_KERNEL} /boot/initrd.img-${L1_KERNEL}"

sudo sha256sum \
  "/var/lib/libvirt/images/agi-nested/direct-boot/vmlinuz-${L1_KERNEL}" \
  "/var/lib/libvirt/images/agi-nested/direct-boot/initrd.img-${L1_KERNEL}"
```

Confirm that each source checksum matches its copied file. Shut down L1 cleanly:

```bash
ssh -i "${HOME}/.ssh/agi_nested" -p 2222 \
  ubuntu@127.0.0.1 'sudo shutdown -h now'
sudo virsh --connect qemu:///system domstate agi-l1-hyper
```

Wait until the state is `shut off`.

## Enable virtual EL2 with direct kernel boot

The tested AGI configuration also requires SVE to be hidden from L1. Without this setting, KVM injects an SVE access trap while Linux starts at virtual EL2 and the vCPU becomes stuck at its exception vector.

Save the inactive domain XML, then update it programmatically. Run this in the same L0 shell where `L1_KERNEL` and `L1_ROOT_UUID` are set:

```bash
sudo virsh --connect qemu:///system dumpxml --inactive \
  agi-l1-hyper > /tmp/agi-l1-hyper.xml

sudo python3 - "$L1_KERNEL" "$L1_ROOT_UUID" <<'PY'
from pathlib import Path
import sys
import xml.etree.ElementTree as ET

kernel_version, root_uuid = sys.argv[1:]
source = Path("/tmp/agi-l1-hyper.xml")
output = Path("/tmp/agi-l1-hyper-direct.xml")
qemu_ns = "http://libvirt.org/schemas/domain/qemu/1.0"
ET.register_namespace("qemu", qemu_ns)

tree = ET.parse(source)
root = tree.getroot()

os_element = root.find("os")
if os_element is None:
    raise SystemExit("The domain XML has no os element")
for child in list(os_element):
    os_element.remove(child)

type_element = ET.SubElement(os_element, "type", {
    "arch": "aarch64",
    "machine": "virt-11.1",
})
type_element.text = "hvm"
boot_directory = "/var/lib/libvirt/images/agi-nested/direct-boot"
ET.SubElement(os_element, "kernel").text = (
    f"{boot_directory}/vmlinuz-{kernel_version}"
)
ET.SubElement(os_element, "initrd").text = (
    f"{boot_directory}/initrd.img-{kernel_version}"
)
ET.SubElement(os_element, "cmdline").text = (
    f"root=UUID={root_uuid} ro rootwait console=ttyAMA0 earlycon"
)

features = root.find("features")
if features is not None:
    acpi = features.find("acpi")
    if acpi is not None:
        features.remove(acpi)

cpu = root.find("cpu")
if cpu is None:
    raise SystemExit("The domain XML has no cpu element")
for feature in list(cpu.findall("feature")):
    if feature.get("name") == "sve":
        cpu.remove(feature)
ET.SubElement(cpu, "feature", {"policy": "disable", "name": "sve"})

for argument in root.findall(f".//{{{qemu_ns}}}arg"):
    if argument.get("value") == "virtualization=off":
        argument.set("value", "virtualization=on")

ET.indent(tree, space="  ")
tree.write(output, encoding="unicode", xml_declaration=True)
print(f"Wrote {output}")
PY
```

Validate, define, and start the direct-boot configuration:

```bash
sudo virt-xml-validate /tmp/agi-l1-hyper-direct.xml domain
sudo virsh --connect qemu:///system define /tmp/agi-l1-hyper-direct.xml
sudo virsh --connect qemu:///system start agi-l1-hyper
```

## Verify KVM inside L1

Connect from **L0** after Ubuntu starts:

```bash
ssh -i "${HOME}/.ssh/agi_nested" -p 2222 ubuntu@127.0.0.1
```

Inside **L1**, verify initialization:

```bash
sudo cloud-init status --wait
hostname
uname -m
uname -r
sudo dmesg | grep -iE 'EL2|VHE|kvm'
ls -l /dev/kvm
```

The relevant output from the tested L1 VM is:

```output
agi-l1-hyper
aarch64
6.8.0-142-generic
[    0.000000] CPU features: detected: HCRX_EL2 register
[    0.036098] CPU: All CPU(s) started at EL2
[    0.122388] kvm [1]: IPA Size Limit: 48 bits
[    0.123583] kvm [1]: GIC system register CPU interface enabled
[    0.124049] kvm [1]: vgic interrupt IRQ9
[    0.124441] kvm [1]: VHE mode initialized successfully
crw-rw---- 1 root kvm 10, 232 Jul 28 15:04 /dev/kvm
```

`All CPU(s) started at EL2`, `VHE mode initialized successfully`, and the presence of `/dev/kvm` confirm that L1 can act as a KVM hypervisor. L1 does not need `kvm-arm.mode=nested` because this path does not create an L3 VM.

## What you've accomplished and what's next

You've booted an Ubuntu L1 hypervisor directly with virtual EL2 exposed, disabled the incompatible SVE exposure, and verified that L1 can access KVM. Next, you'll install the guest hypervisor tools and create L2 using KVM.
