import yaml
import os

def createpod(nodes,pods_details,i):
	name = str(pods_details['name'])
	image = str(pods_details['image'])
	cpu = pods_details['cpus']
	gpu = pods_details['gpus']
	memory = pods_details['memory']
	mem = str(memory)+"Mi"
	n = i
	new = ["203.250.170.31"]
	data=[{
	'apiVersion': 'kubeflow.org/v1',
	'kind': 'TFJob',
	"metadata":{"name": name},
	"spec":{
	  "tfReplicaSpecs": {
	    "PS": {
	      "replicas": 1,
	      "restartPolicy": "Never",
	      "template": {
	        "spec": {
	          "containers": [
	            {
	              "name": name,
	              "image": image,
	              "resources": {
	                "requests": {
	                  "cpu": cpu,
	                  "memory": mem                          
	                },
                        "limits": {
                          "cpu": cpu,
                          "memory": mem                          
                        }

	              }
	            }
        	  ],
	          "affinity": {
                  "nodeAffinity": {
                    "requiredDuringSchedulingIgnoredDuringExecution": {
                      "nodeSelectorTerms": [
                        {
                           "matchExpressions": [
                             {
                               "key": "kubernetes.io/hostname",
                               "operator": "In",
                               "values": nodes  #nodes  #["malaysia-node","pakistan-node"]
                          }
                        ]
                      }
                    ]
                  }
                }
              }
	     }
	    }
	    },
	    "Worker": {
	      "replicas": n,
	      "restartPolicy": "Never",
	      "template": {
	        "spec": {
	          "containers": [
	            {
	              "name": name,
	              "image": image,
	              "resources": {
        	        "requests": {
	                  "cpu": cpu,
	                  "memory": mem,
                          "nvidia.com/gpu": gpu
	                },
                        "limits": {
                          "cpu": cpu,
                          "memory": mem,
                          "nvidia.com/gpu": gpu
                        }
	              }
	            }
	          ],
	          "affinity": {
	            "nodeAffinity": {
	              "requiredDuringSchedulingIgnoredDuringExecution": {
	                "nodeSelectorTerms": [
	                  {
        	            "matchExpressions": [
                	      {
                        	"key": "kubernetes.io/hostname",
	                        "operator": "In",
        	                "values": nodes
        	              }
                	    ]
	                  }
        	        ]
	              }
	            }
	          }
	        }
	      }
	    }
	  }
	}
	}
	]

	with open(f'tensor.yaml', 'w',) as f :
		yaml.dump_all(data,f,sort_keys=False) 
		print('Written to file successfully')
	cmd = 'kubectl apply -f tensor.yaml'
	os.system(cmd)
	return {"status":"pods created"}

