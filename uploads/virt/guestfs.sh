#!/usr/bin/env bash

name=$1
ip=$2
hostname=$3
hwaddr_em2=$4
hwaddr_em1=$5

netmask=255.255.255.0

x=`echo $ip | awk -F. '{print $1"."$2"."$3}'`
gateway="$x.1"

# ���������, �����޷��������޸ľ���.
virsh define /etc/libvirt/qemu/$name.xml || exit 1

# �޸�ϵͳ����, ����:
# 1. �޸�������;
# 2. �޸���������(����HWADDR��ԭ����ϵͳ���԰�eth���em);
# 3. �޸�·����Ϣ;
# 4. ɾ��/etc/udev/rules.d/70-persistent-net.rules;
# Ȼ������

guestfish --rw -d $name <<_EOF_
run
mount /dev/domovg/root /
mount /dev/datavg/home /home/
command "sed -i 's/HOSTNAME=.*/HOSTNAME=${hostname}/g' /etc/sysconfig/network"

write /etc/sysconfig/network-scripts/ifcfg-em2 "DEVICE=em2\nHWADDR=${hwaddr_em2}\nBOOTPROTO=static\nIPADDR=$ip\nNETMASK=$netmask\nONBOOT=yes\nTYPE=Ethernet"

write /etc/sysconfig/network-scripts/ifcfg-em1 "DEVICE=em1\nHWADDR=${hwaddr_em1}"

write /etc/sysconfig/network-scripts/route-em2 "192.168.0.0/16 via 10.19.28.1\n10.0.0.0/8 via 10.19.28.1\n100.64.0.0/16 via 10.19.28.1\n0.0.0.0/0 via 10.19.28.1"

command "/bin/rm -rf /etc/udev/rules.d/70-persistent-net.rules"
_EOF_