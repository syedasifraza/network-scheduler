from kubernetes import client, config
#rom getgpu import gpu_used
#rom getcpu import cpu_used
#rom getmemory import memory_used
#rom createpods import pods
#rom getnodes import getnodes

def main():

   #pod_details = {'name':name,'image':image,'cpus':req_cpu,'gpus':req_gpu,'memory':req_mem}
   config.load_kube_config(config_file='./config')
   api_instance = client.CoreV1Api()
   node_list = api_instance.list_node()

   #esources={}
   #esourcesNodes={}
   #electedZone="None"
   #electedNode="None"

   #print(node_list)
   
   for node in node_list.items:
      if("master"!=node.metadata.labels["Zone"] and "ceph"!=node.metadata.labels["Zone"]):
        print("Node: "+node.metadata.name)
        print("CPUs: "+node.status.capacity['cpu'])
      else:
        print("Master or CEPH Storage Node")


if __name__ == '__main__':
    main()

