---
title: Create the nested L2 guest
description: Install KVM tools inside L1 and boot an Ubuntu 24.04 Arm64 guest with QEMU user-mode networking.
weight: 4

### FIXED, DO NOT MODIFY
layout: learningpathall
---

## Install the hypervisor tools in L1

Run the commands on this page **inside L1**. From L0, connect with:

```bash
ssh -i "${HOME}/.ssh/agi_nested" -p 2222 ubuntu@127.0.0.1
```

Check the host name before continuing:

```bash
hostname
```

The output must be:

```output
agi-l1-hyper
```

Install the Ubuntu virtualization tools:

```bash
sudo apt update
sudo apt install -y qemu-kvm qemu-utils qemu-efi-aarch64 \
  libvirt-daemon-system libvirt-clients virtinst \
  cloud-image-utils curl
sudo systemctl enable --now libvirtd
sudo virt-host-validate qemu
qemu-system-aarch64 --version
```

The `/dev/kvm` existence and access checks must pass. The IOMMU and secure-guest checks can report warnings; neither feature is required for this example.

The Ubuntu 24.04 QEMU package is sufficient for L2 because L2 is an ordinary guest. On the tested L1 system, the version was:

```output
QEMU emulator version 8.2.2 (Debian 1:8.2.2+ds-0ubuntu1.18)
```

## Prepare the L2 image and key

Create a separate SSH key inside L1 for connecting to L2:

```bash
mkdir -p "${HOME}/.ssh"
chmod 700 "${HOME}/.ssh"
if [ ! -f "${HOME}/.ssh/agi_nested_l2" ]; then
  ssh-keygen -t ed25519 -f "${HOME}/.ssh/agi_nested_l2" -N ""
fi
```

Download an Ubuntu 24.04 Arm64 image and expand its virtual size to 20 GiB:

```bash
(
set -e
VM_DIRECTORY=/var/lib/libvirt/images/agi-nested
sudo mkdir -p "$VM_DIRECTORY"
test ! -e "${VM_DIRECTORY}/agi-l2-guest.qcow2"

sudo curl --fail --location \
  https://cloud-images.ubuntu.com/releases/noble/release/ubuntu-24.04-server-cloudimg-arm64.img \
  --output "${VM_DIRECTORY}/agi-l2-guest.qcow2"

sudo qemu-img resize "${VM_DIRECTORY}/agi-l2-guest.qcow2" 20G
sudo qemu-img info "${VM_DIRECTORY}/agi-l2-guest.qcow2"
)
```

## Create the L2 cloud-init seed

Create the L2 user, hostname, and DHCP configuration:

```bash
(
set -e
VM_DIRECTORY=/var/lib/libvirt/images/agi-nested
SSH_PUBLIC_KEY="$(cat "${HOME}/.ssh/agi_nested_l2.pub")"
SEED_DIRECTORY=$(mktemp -d)
test ! -e "${VM_DIRECTORY}/agi-l2-guest-seed.iso"

cat > "${SEED_DIRECTORY}/user-data" <<EOF
#cloud-config
hostname: agi-l2-guest
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
instance-id: agi-l2-guest
local-hostname: agi-l2-guest
EOF

cat > "${SEED_DIRECTORY}/network-config" <<'EOF'
version: 2
ethernets:
  nestednic:
    match:
      macaddress: "52:54:00:a6:02:01"
    dhcp4: true
EOF

sudo cloud-localds --network-config="${SEED_DIRECTORY}/network-config" \
  "${VM_DIRECTORY}/agi-l2-guest-seed.iso" \
  "${SEED_DIRECTORY}/user-data" "${SEED_DIRECTORY}/meta-data"
rm -r "$SEED_DIRECTORY"
)
```

## Configure QEMU user-mode networking

The tested AGI configuration uses QEMU's built-in user-mode network for L2. It provides DHCP and outbound connectivity without relying on the host kernel's libvirt NAT firewall rules. TCP port 2222 on L1 is forwarded to L2's SSH port.

First generate the domain XML without a libvirt-managed network:

```bash
sudo virt-install \
  --connect qemu:///system \
  --name agi-l2-guest \
  --virt-type kvm \
  --arch aarch64 \
  --machine virt \
  --cpu host-passthrough \
  --vcpus 2 \
  --memory 2048 \
  --import \
  --osinfo generic \
  --boot uefi \
  --disk path=/var/lib/libvirt/images/agi-nested/agi-l2-guest.qcow2,format=qcow2,bus=virtio \
  --disk path=/var/lib/libvirt/images/agi-nested/agi-l2-guest-seed.iso,device=cdrom,format=raw \
  --network none \
  --graphics none \
  --noautoconsole \
  --print-xml > "${HOME}/agi-l2-guest.xml"
```

Add the QEMU network arguments with Python. This avoids indentation and XML namespace errors when editing the file manually:

```bash
python3 - "${HOME}/agi-l2-guest.xml" <<'PY'
import sys
import xml.etree.ElementTree as ET

path = sys.argv[1]
qemu_namespace = "http://libvirt.org/schemas/domain/qemu/1.0"
ET.register_namespace("qemu", qemu_namespace)

tree = ET.parse(path)
root = tree.getroot()
commandline = ET.SubElement(root, f"{{{qemu_namespace}}}commandline")

for value in (
    "-netdev",
    "user,id=l2net,hostfwd=tcp:127.0.0.1:2222-:22",
    "-device",
    "virtio-net-device,netdev=l2net,mac=52:54:00:a6:02:01",
):
    ET.SubElement(commandline, f"{{{qemu_namespace}}}arg", {"value": value})

tree.write(path, encoding="unicode")
PY

sudo virt-xml-validate "${HOME}/agi-l2-guest.xml" domain
```

Use `virtio-net-device` exactly as shown. This device attaches directly to the Arm `virt` machine and does not require a manually created PCIe root port.

## Boot and connect to L2

Define and start the L2 domain:

```bash
sudo virsh --connect qemu:///system define \
  "${HOME}/agi-l2-guest.xml"
sudo virsh --connect qemu:///system start agi-l2-guest
sudo virsh --connect qemu:///system list --all
sudo ss -ltnp 'sport = :2222'
```

The domain must be `running`, and QEMU must listen on `127.0.0.1:2222`.

L2 can take about two minutes to complete its first boot. Watch the serial console if needed:

```bash
sudo virsh --connect qemu:///system console agi-l2-guest
```

Press **Ctrl+]** to leave the console. When cloud-init reaches its final stage, connect from L1:

```bash
ssh -i "${HOME}/.ssh/agi_nested_l2" -p 2222 ubuntu@127.0.0.1
```

Inside L2, verify initialization:

```bash
sudo cloud-init status --wait
hostname
uname -m
cat /etc/os-release
```

Confirm the cloud-init status is `done`, the host name is `agi-l2-guest`, the architecture is `aarch64`, and the operating system is Ubuntu 24.04.

## What you've accomplished and what's next

You've booted an Ubuntu guest inside the L1 hypervisor and connected to it through a local SSH port forward. Next, you'll confirm that both VM layers use KVM and run a workload in L2.
