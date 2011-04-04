#!/usr/bin/env python

import sys
import time
import logging
import socket
import boto
import fabric.api
import paramiko

logger = logging.getLogger(__name__)

def _wait_for_instance(instance):
    while instance.state != 'running':
        logger.debug('waiting for instance %s', instance)
        time.sleep(10)
        instance.update()

def _wait_for_reservation(reservation):
    for instance in reservation.instances:
        _wait_for_instance(instance)

def _wait_for_ssh(host, key_filename):
    retries = 10
    while True:
        client = paramiko.SSHClient()
        client.load_system_host_keys()
        client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
        tic = time.time()
        try:
            client.connect(hostname=host, username='ubuntu', key_filename=key_filename, timeout=30)
        except (socket.error, EOFError), e:
            logger.debug('ssh not ready, with error %s. retries left %d' % (e, retries))
            toc = time.time()
            diff = toc - tic
            if diff < 30:
                time.sleep(30 - diff)
            retries-= 1
            if retries == 0:
                logger.critical('ssh timed out to host %s' % host)
                sys.exit(1)
            else:
                logger.debug('ssh connected')
                continue
        else:
            return
        finally:
            client.close()

def _wait_for_cmd_for_instances(instances, commands):
    for i, instance in enumerate(instances):
        logger.info('machine: %03d: %s', i, instance)
        host = instance.dns_name
        _wait_for_ssh(host, key_filename)
        for command in commands:
            _wait_for_cmd(host, key_filename, command)

def _wait_for_cmd(host, key_filename, command):
    with fabric.api.settings(fabric.api.hide('warnings', 'running', 'stdout', 'stderr'), 
            host_string=host, key_filename=key_filename, user='ubuntu', warn_only=True):
        success = False
        while not success:
            output = fabric.api.run(command)
            success = output.succeeded
            logger.debug('cmd output: %s' % success)
            if not success:
                logger.debug('waiting for %s' % command)
                time.sleep(60)
            else:
                logger.debug('%s ready' % command)

def main(keypair, key_filename, user_data_filename, num_nodes):
    conn = boto.connect_ec2()
    user_data = open(user_data_filename, 'r').read()

    # instance-store ami ami-7000f019
    master_reservation = conn.run_instances("ami-ccf405a5",
        min_count = 1,
        max_count = 1,
        key_name = keypair,
        user_data = user_data,
        instance_type='t1.micro',
        )

    _wait_for_reservation(master_reservation)
    _wait_for_cmd_for_instances(master_reservation.instances, ['riak-admin wait-for-service riak_kv riak@`hostname -f`'])

    master_internal_ip = master_reservation.instances[0].private_dns_name
    logger.info('master node is %s' % master_reservation.instances[0].dns_name)
    user_data += '\nriak-admin wait-for-service riak_kv riak@`hostname -f`\n'
    user_data += '\npython -c "import time, random; time.sleep(random.choice(range(1500)));"\n'
    #user_data += '\nriak-admin wait-for-service riak_kv riak@%s\n' % master_internal_ip
    user_data += 'riak-admin join riak@%s\n' % master_internal_ip

    cluster_reservation = conn.request_spot_instances(0.02, "ami-ccf405a5",
        count = num_nodes,
        key_name = keypair,
        user_data = user_data,
        instance_type='t1.micro',
        )

if __name__ == '__main__':
    logging.basicConfig(level=logging.DEBUG)
    logging.getLogger('boto').setLevel(logging.CRITICAL)
    logging.getLogger('paramiko').setLevel(logging.CRITICAL)
    logging.getLogger('fabric').setLevel(logging.CRITICAL)

    args = sys.argv[1:]
    keypair, key_filename, user_data_filename, num_nodes  = args
    num_nodes = int(num_nodes)
    num_nodes-= 1 # we always have a master

    main(keypair, key_filename, user_data_filename, num_nodes)
