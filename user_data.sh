#!/bin/bash
set -e -x
exec > >(tee /var/log/user-data.log|logger -t user-data -s 2>/dev/console) 2>&1
export DEBIAN_FRONTEND=noninteractive

apt-get update && apt-get upgrade -y

apt-get install -y wget

wget http://downloads.basho.com/riak/riak-0.14/riak_0.14.0-1_i386.deb
dpkg -i riak_0.14.0-1_i386.deb

sudo wget "https://riak-cluster-chef.s3.amazonaws.com/app.config"
sudo wget "https://riak-cluster-chef.s3.amazonaws.com/vm.args"
cat app.config > /etc/riak/app.config
cat vm.args > /etc/riak/vm.args
riak start
