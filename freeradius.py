#!/usr/bin/env python
# -*- coding: utf-8 -*-

import signal
import re
import subprocess


config = {
    'port': 18121,
    'secret': 'adminsecret',
    'host': 'localhost',
    'timeout': 1,
    'stat_type': 1
}


def configer(conf):
    for node in conf.children:
        if node.key == 'Host':
            config['host'] = node.values[0]
        if node.key == 'Port':
            try:
                config['port'] = int(node.values[0])
            except:
                collectd.warning("can not use provided port {0}"
                                 .format(node.values[0]))
        if node.key == 'Secret':
            config['secret'] = node.values[0]
        if node.key == 'Statistics_Type':
            try:
                config['stat_type'] = int(node.values[0])
            except:
                collectd.warning("can not use provided stats type {0}"
                                 .format(node.values[0]))


def get_metrics():

    def _convert_name(name):
        return name.replace('FreeRADIUS-Total-', '').replace('-', '_').lower()

    cmd = ('echo "Message-Authenticator = 0x00, '
           'FreeRADIUS-Statistics-Type = {stat_type}, '
           'Response-Packet-Type = Access-Accept" | '
           'radclient -t {timeout} -x {host}:{port} status {secret}'
           .format(
                timeout=config['timeout'],
                port=config['port'],
                secret=config['secret'],
                host=config['host'],
                stat_type=config['stat_type']))
    child = subprocess.Popen(cmd, shell=True, stdout=subprocess.PIPE)
    stdout, stderr = child.communicate()
    metrics = {}
    found_metrics = re.findall(r'(FreeRADIUS-Total.*) = (\d*)', stdout)
    for metric_couple in found_metrics:
        try:
            metrics[_convert_name(metric_couple[0])] = int(metric_couple[1])
        except:
            collectd.warning(
            "can not collect couple: {0}".format(', '.join(metric_couple)))
    return metrics


def reader():
    metrics = get_metrics()
    for type, value in metrics.items():
        dispatch_value(type, value)


def dispatch_value(val_type, value, metric_type='gauge'):
    val = collectd.Values(plugin='freeradius')
    val.type = metric_type
    val.type_instance = val_type
    val.values = [value]
    val.dispatch()


if __name__ == '__main__':
    print(get_metrics())
else:
    import collectd
    # http://giovannitorres.me/using-collectd-python-and-graphite-to-graph-slurm-partitions.html
    collectd.register_init(signal.signal(signal.SIGCHLD, signal.SIG_DFL))
    collectd.register_config(configer)
    collectd.register_read(reader)
