#!/usr/bin/env python

import time
import random
import json
import subprocess

from csv import DictReader

from kubernetes import client, config, watch
from logging import basicConfig, getLogger, INFO

logger = getLogger("meetup-scheduler")

config.load_kube_config()
v1=client.CoreV1Api()

_NOSCHEDULE_TAINT = "NoSchedule"
scheduler_name = "foobar"

def nodes_available():
    ready_nodes = []
    for n in v1.list_node().items:
            for status in n.status.conditions:
                if status.status == "True" and status.type == "Ready":
                    ready_nodes.append(n.metadata.name)
            cpu_r,memory_r=test_free(n.metadata.name)
            print("Node Name: "+n.metadata.name+"    Free CPUs: "+str(cpu_r)+"   Free Memory: "+str(memory_r))

    return ready_nodes


def get_ready_nodes(v1_client, filtered=True):
    ready_nodes = []
    try:
        for n in v1_client.list_node().items:
            if n.metadata.labels.get("noCustomScheduler") == "yes":
                logger.info(f"Skipping Node {n.metadata.name} since it has noCustomScheduler label")
                continue
            if filtered:
                if not n.spec.unschedulable:
                    no_schedule_taint = False
                    if n.spec.taints:
                        for taint in n.spec.taints:
                            if _NOSCHEDULE_TAINT == taint.to_dict().get("effect", None):
                                no_schedule_taint = True
                                break
                    if not no_schedule_taint:
                        for status in n.status.conditions:
                            if status.status == "True" and status.type == "Ready" and n.metadata.name and n.metadata.labels['Zone']=='A':
                                ready_nodes.append(n.metadata.name)
                                #print(ready_nodes)
                    else:
                        logger.error("NoSchedule taint effect on node %s", n.metadata.name)
                        print(n.metadata.name)
                else:
                    logger.error("Scheduling disabled on %s ", n.metadata.name)
            else:
                if n.metadata.name:
                    ready_nodes.append(n.metadata.name)
        logger.info("Nodes : %s, Filtered: %s", ready_nodes, filtered)
    except ApiException as e:
        logger.error(json_loads(e.body)["message"])
        ready_nodes = []
    return ready_nodes



def get_schedulable_node():
    node_list = get_ready_nodes(v1)
    if not node_list:
        return None
    available_nodes = list(set(node_list))
    print(available_nodes)
    #return random.choice(available_nodes)

def cpu_free():
    with open('/tmp/cpu.csv','w') as f_obj, open('/tmp/cpu.csv', 'r') as read_obj:
       subprocess.run(["kubectl-view-allocations", "-o", "csv", "-r", "cpu", "-g", "node"],stdout=f_obj,text=True)
       csv_dict_reader = DictReader(read_obj)
       remove_row_1 = next(csv_dict_reader)
       for row,n in zip(csv_dict_reader,v1.list_node().items):            
           print(row['node'],row['Free'])
           print(n.metadata.labels['Zone'])

def memory_free():
    with open('/tmp/memory.csv','w') as f_obj, open('/tmp/memory.csv', 'r') as read_obj:
       subprocess.run(["kubectl-view-allocations", "-o", "csv", "-r", "memory", "-g", "node"],stdout=f_obj,text=True)
       csv_dict_reader = DictReader(read_obj)
       remove_row_1 = next(csv_dict_reader)
       #for row in csv_dict_reader:
       #    print(row['node'],row['Free'])

def test_free(node):
    cpu_return = ""
    memory_return=""
    with open('/tmp/cpu.csv','w') as cpu_obj, open('/tmp/cpu.csv', 'r') as cpu_read_obj, open('/tmp/memory.csv','w') as memory_obj, open('/tmp/memory.csv', 'r') as memory_read_obj:
       subprocess.run(["kubectl-view-allocations", "-o", "csv", "-r", "cpu", "-g", "node"],stdout=cpu_obj,text=True)
       subprocess.run(["kubectl-view-allocations", "-o", "csv", "-r", "memory", "-g", "node"],stdout=memory_obj,text=True)       
       cpu_reader = DictReader(cpu_read_obj)
       memory_reader = DictReader(memory_read_obj)
       remove_cpurow_1 = next(cpu_reader)
       remove_memoryrow_1 = next(memory_reader)
       for rowcpu,rowmemory in zip(cpu_reader,memory_reader):
           if node == rowcpu['node']:
              cpu_return=rowcpu['Free']
              memory_return=rowmemory['Free']
              break
           #print(rowcpu['node'],rowcpu['Free'])
           #print(rowmemory['node'],rowmemory['Free'])
       return cpu_return,memory_return

def main():
    get_schedulable_node()
    #cpu_free()

    #nodes_available()
    #cpu_free()
    #memory_free()
    #print (nodes_available())

if __name__ == '__main__':
    main()

