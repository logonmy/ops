#!/usr/bin/env bash
sudo yum install -y git redis python-pip python-simplejson python-requests MySQL-python python-lxml libvirt-python libxml2-python python-dateutil
sudo pip install --upgrade pip
sudo pip install gevent ncclient docker-py kazoo falcon peewee gunicorn pyzabbix redis kazoo pika kafka-python autojenkins upyun ldap7 ansible libxml2-python elasticsearch libvirt-python simplejson requests python-dateutil lxml

service redis start

mkdir -p /data

cd /data
git clone git://github.com/xiaomatech/ops.git
git submodule update --init --recursive

