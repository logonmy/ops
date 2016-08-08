#!/usr/bin/env bash
sudo yum install -y git redis python-pip python-simplejson python-requests MySQL-python python-lxml libvirt-python libxml2-python python-dateutil net-snmp net-snmp-utils net-snmp-python
sudo pip install --upgrade pip
sudo pip install gevent ncclient docker-py kazoo falcon peewee gunicorn pyzabbix redis kazoo pika kafka-python autojenkins upyun ldap3 ansible

service redis start

mkdir -p /data

cd /data
git clone git://github.com/xiaomatech/ops.git
git submodule update --init --recursive

