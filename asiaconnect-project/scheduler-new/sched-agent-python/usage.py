from kubernetes import client, config
from getgpu import gpu_used
from getcpu import cpu_used
from getmemory import memory_used
from createpods import pods
from createpods_t import createpod
from getnodes import getnodes
from networkpass import networkpass

def main(name, image, req_cpu, req_gpu, req_mem, req_nodes):
    print(name)
    print(image)
    print(req_cpu)
    print(req_gpu)
    print(req_mem)
    print(req_nodes)

    pod_details = {'name':name,'image':image,'cpus':req_cpu,'gpus':req_gpu,'memory':req_mem}
    config.load_kube_config(config_file='./config')
    api_instance = client.CoreV1Api()   
    node_list = api_instance.list_node()
    
    resources={}
    resourcesNodes={}
    selectedZone="None"
    selectedNode="None"
    testNodes="None"


    for node in node_list.items:
      if("master"!=node.metadata.labels["Zone"] and "ceph"!=node.metadata.labels["Zone"]):
        NODE=node.metadata.name
        capacity_cpu=int(node.status.capacity['cpu'])
        used_cpu=cpu_used(NODE)
        avail_cpu=int((capacity_cpu - (used_cpu/1000)))
        

        capacity_memory=node.status.capacity['memory']
        capacity_memory=(int(capacity_memory[:-2])/1000)
        used_memory=memory_used(NODE)
        avail_memory=int(capacity_memory-used_memory)

        if("hardware-type" in node.metadata.labels):

          gpu_position = len(node.status.capacity)
          capacity_gpu=int(node.status.capacity['nvidia.com/gpu'])
          used_gpu=int(gpu_used(NODE,str(gpu_position)))
          avail_gpu=capacity_gpu-used_gpu
        else:
          avail_gpu=0
       
        if(not resources and avail_cpu >= req_cpu and avail_memory >= req_mem and avail_gpu >= req_gpu):
          resources[node.metadata.labels["Zone"]]=[{"totalResources": {"avail_cpus":avail_cpu, "avail_memory":avail_memory, "avail_gpus":avail_gpu}}]
          resourcesNodes[node.metadata.labels["Zone"]]=[{"node_name":NODE, "avail_cpus":avail_cpu, "avail_memory":avail_memory, "avail_gpus":avail_gpu}]

        else:
          check=0
          for zones in resources:
            if(zones == node.metadata.labels["Zone"] and avail_cpu >= req_cpu and avail_memory >= req_mem and avail_gpu >= req_gpu):
              resourcesNodes[zones].append({"node_name":NODE,"avail_cpus":avail_cpu, "avail_memory":avail_memory, "avail_gpus":avail_gpu})
              avail_cpu=avail_cpu+resources[zones][0]["totalResources"]["avail_cpus"]
              avail_gpu=avail_gpu+resources[zones][0]["totalResources"]["avail_gpus"]
              avail_memory=avail_memory+resources[zones][0]["totalResources"]["avail_memory"]
              resources[zones]=[{"totalResources": {"avail_cpus":avail_cpu, "avail_memory":avail_memory, "avail_gpus":avail_gpu}}]
              
             
              check=1
          if(check == 0 and avail_cpu >= req_cpu and avail_memory >= req_mem and avail_gpu >= req_gpu):
            resources[node.metadata.labels["Zone"]]=[{"totalResources": {"avail_cpus":avail_cpu, "avail_memory":avail_memory, "avail_gpus":avail_gpu}}]
            resourcesNodes[node.metadata.labels["Zone"]]=[{"node_name":NODE,"avail_cpus":avail_cpu, "avail_memory":avail_memory, "avail_gpus":avail_gpu}]

    if(len(resourcesNodes)>0):
      selectedNode=getnodes(resourcesNodes,req_nodes)
      testNodes=networkpass(selectedNode+[str(req_nodes)])
      #for i in range(req_nodes):
      #   pod_response = pods(testNodes,pod_details, i)
      pod_response = createpod(testNodes,pod_details, req_nodes)
      print(testNodes)
      return(testNodes)
    else:
      #print("No resource found!")
      #return {"status":resourcesNodes}
      return {"status":"No Resource Found!"}

#if __name__ == '__main__':
#    main()
