import json
import subprocess
import time
from kubernetes import config, watch
from kubernetes.client import ApiClient, CoreV1Api, V1ObjectReference, V1ObjectMeta, V1Binding, Configuration, BatchV1Api
from kubernetes.client.rest import ApiException, RESTClientObject

from csv import DictReader
from logging import basicConfig, getLogger, INFO

formatter = " %(asctime)s | %(levelname)-6s | %(process)d | %(threadName)-12s |" \
            " %(thread)-15d | %(name)-30s | %(filename)s:%(lineno)d | %(message)s |"
basicConfig(level=INFO, format=formatter)
logger = getLogger("meetup-scheduler")

configuration = Configuration()
configuration.host = "localhost:8888"

V1_CLIENT = None  # type: CoreV1Api
v1 = None
SCHEDULE_STRATEGY = "schedulingStrategy=tfjob"
_NOSCHEDULE_TAINT = "NoSchedule"


def test_free(v1_client, total_req_resources):

    with open('/tmp/cpu.csv','w') as cpu_obj, open('/tmp/cpu.csv', 'r') as cpu_read_obj, open('/tmp/memory.csv','w') as memory_obj, open('/tmp/memory.csv', 'r') as memory_read_obj:
       subprocess.run(["kubectl-view-allocations", "-o", "csv", "-r", "cpu", "-g", "node"],stdout=cpu_obj,text=True)
       subprocess.run(["kubectl-view-allocations", "-o", "csv", "-r", "memory", "-g", "node"],stdout=memory_obj,text=True)
       cpu_reader = DictReader(cpu_read_obj)
       memory_reader = DictReader(memory_read_obj)
       remove_cpurow_1 = next(cpu_reader)
       remove_memoryrow_1 = next(memory_reader)
       logger.info("Inside Test Free")
       for n, rowcpu,rowmemory in zip(v1_client.list_node().items, cpu_reader,memory_reader):
           logger.info("Node in V1: %s, Node in Other: %s", n.metadata.name, rowcpu['node'])

           #memoryfree = ((int(rowmemory['Free'][:-3])/1024)/1024)/1024
           #cpufree = float(rowcpu['Free'])
           #if float(total_req_resources['cpu']) < cpufree and int(total_req_resources['memory']) < memoryfree:
           #   logger.info("Required CPUs and Memory enough on this node: %s", rowcpu['node'])
           #   logger.info(n.metadata.labels['Zone'])
           #   break



def get_ready_nodes(v1_client, total_req_resources, per_node_resources, filtered=True):
    ready_nodes = []
    zones = {}

    with open('/tmp/cpu.csv','w') as cpu_obj, open('/tmp/cpu.csv', 'r') as cpu_read_obj, open('/tmp/memory.csv','w') as memory_obj, open('/tmp/memory.csv', 'r') as memory_read_obj:
       subprocess.run(["kubectl-view-allocations", "-o", "csv", "-r", "cpu", "-g", "node"],stdout=cpu_obj,text=True)
       subprocess.run(["kubectl-view-allocations", "-o", "csv", "-r", "memory", "-g", "node"],stdout=memory_obj,text=True)
       cpu_reader = DictReader(cpu_read_obj)
       memory_reader = DictReader(memory_read_obj)
       remove_cpurow_1 = next(cpu_reader)
       remove_memoryrow_1 = next(memory_reader)
       logger.info("Inside Test Free")
       check_selected = 0
       for n, rowcpu,rowmemory in zip(v1_client.list_node().items, cpu_reader,memory_reader):
           memoryfree = ((int(rowmemory['Free'][:-3])/1024)/1024)/1024
           cpufree = float(rowcpu['Free'])
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
                           if status.status == "True" and status.type == "Ready" and float(total_req_resources['cpu']) < cpufree and int(total_req_resources['memory']) < memoryfree:
                               ready_nodes = [n.metadata.name]
                               check_selected = 1
                               logger.info("Node in V1: %s, Node in Other: %s", n.metadata.name, rowcpu['node'])
                               break
                           elif status.status == "True" and status.type == "Ready" and float(per_node_resources['cpu']) < cpufree and int(per_node_resources['memory']) < memoryfree:
                               ready_nodes.append(n.metadata.name)
                               if (not zones):
                                   zones[n.metadata.labels['Zone']] = [{"avail_cpu":cpufree, "avail_memory":memoryfree}]
                               else:
                                   check = 0
                                   for z in zones:
                                       if z == n.metadata.labels['Zone']:
                                           c = cpufree + float(zones[z][0]['avail_cpu'])
                                           m = memoryfree + float(zones[z][0]['avail_memory'])                                           
                                           zones[z][0] = {"avail_cpu":c, "avail_memory":m}
                                           check = 1
                                   if check == 0:
                                       zones[n.metadata.labels['Zone']]=[{"avail_cpu":cpufree, "avail_memory":memoryfree}]
                               break
                       if check_selected == 1:
                           break
                   else:
                       logger.error("NoSchedule taint effect on node %s", n.metadata.name)
               else:
                   logger.error("Scheduling disabled on %s ", n.metadata.name)
           else:
               if n.metadata.name:
                   ready_nodes.append(n.metadata.name)
       logger.info("Zones : %s", zones)


    




def watch_pod_events():
    V1 = CoreV1Api()
    v1 = BatchV1Api()
    while True:
        try:
            logger.info("Checking for pod events....")
            try:
                watcher = watch.Watch()

                podsgroup = []
                uid = None

                total_req_resources = {"cpu": 0, "memory": 0, "gpu": 0}
                per_node_resources = {"mincpu": 0, "minmemory": 0, "mingpu": 0}

                for event in watcher.stream(V1.list_pod_for_all_namespaces, label_selector=SCHEDULE_STRATEGY, timeout_seconds=5):

                    logger.info(f"Event: {event['type']} {event['object'].kind}, {event['object'].metadata.namespace}, {event['object'].metadata.name}, {event['object'].status.phase}")                   

                    if event["object"].status.phase == "Pending" and len(podsgroup) <= 0 and uid == None:
                         logger.info("Condition True")
                         podsgroup.append(event['object'].metadata.name)
                         uid = event['object'].metadata.owner_references[0].uid
 
                         total_req_resources ['cpu'] = event['object'].spec.containers[0].resources.limits['cpu']
                         total_req_resources ['memory'] = str(int(event['object'].spec.containers[0].resources.limits['memory'][:-2]))
                         total_req_resources ['gpu'] = event['object'].spec.containers[0].resources.limits['nvidia.com/gpu']

                         per_node_resources ['cpu'] = event['object'].spec.containers[0].resources.limits['cpu']
                         per_node_resources ['memory'] = str(int(event['object'].spec.containers[0].resources.limits['memory'][:-2]))
                         per_node_resources ['gpu'] = event['object'].spec.containers[0].resources.limits['nvidia.com/gpu']

                    elif event["object"].status.phase == "Pending" and uid ==  event['object'].metadata.owner_references[0].uid: #podsgroupname == event['object'].metadata.annotations['kubernetes.io/mykey']:
                         logger.info("Else if Condition True")
                         podsgroup.append(event['object'].metadata.name)
                          
                         total_req_resources ['cpu'] = str(int(total_req_resources['cpu']) + int(event['object'].spec.containers[0].resources.limits['cpu']))
                         total_req_resources ['memory'] = str(int(total_req_resources['memory']) + int(event['object'].spec.containers[0].resources.limits['memory'][:-2]))
                         total_req_resources ['gpu'] = str(int(total_req_resources['gpu']) + int(event['object'].spec.containers[0].resources.limits['nvidia.com/gpu']))
 
                         if int(event['object'].spec.containers[0].resources.limits['cpu']) > int(per_node_resources['cpu']):
                             per_node_resources ['cpu'] = event['object'].spec.containers[0].resources.limits['cpu']

                         if int(event['object'].spec.containers[0].resources.limits['memory'][:-2]) > int(per_node_resources['memory']):
                             per_node_resources ['memory'] = str(int(event['object'].spec.containers[0].resources.limits['memory'][:-2]))

                         if int(event['object'].spec.containers[0].resources.limits['nvidia.com/gpu']) > int(per_node_resources['gpu']):
                             per_node_resources ['gpu'] = event['object'].spec.containers[0].resources.limits['nvidia.com/gpu']

                         logger.info(per_node_resources['cpu'])
 
                    else:
                         logger.info("Condition False")
                get_ready_nodes(V1, total_req_resources, per_node_resources)
                #schedule_pods(V1, podsgroup)
                
            except:
                logger.exception("Ignoring Exception")
            finally:
                del watcher
        except:
            logger.exception("Ignoring Exception & listening for pod events")

def main():
    watch_pod_events()


if __name__ == "__main__":
    config.load_kube_config()
    main()
