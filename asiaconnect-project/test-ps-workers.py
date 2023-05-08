from kubernetes import client, config
from kubernetes.client import V1PodSpec, V1Container, V1ResourceRequirements, V1ObjectMeta, V1JobSpec, V1alpha1TFJob, V1alpha1TFJobSpec, V1alpha1TFJobList

config.load_kube_config()

# Define the YAML configuration for the PS container
ps_container = V1Container(
    name="ps",
    image="tensorflow/tensorflow:latest-gpu",
    command=["python"],
    args=["train.py", "--ps"],
    resources=V1ResourceRequirements(
        requests={"cpu": "0.5", "memory": "1Gi"},
        limits={"cpu": "1", "memory": "2Gi"}
    )
)

# Define the YAML configuration for the worker container
worker_container = V1Container(
    name="worker",
    image="tensorflow/tensorflow:latest-gpu",
    command=["python"],
    args=["train.py", "--worker", "--ps-host", "ps"],
    resources=V1ResourceRequirements(
        requests={"cpu": "1", "memory": "2Gi"},
        limits={"cpu": "2", "memory": "4Gi"}
    )
)

# Define the YAML configuration for the TFJob
tfjob = V1alpha1TFJob(
    api_version="kubeflow.org/v1alpha1",
    kind="TFJob",
    metadata=V1ObjectMeta(name="my-tfjob"),
    spec=V1alpha1TFJobSpec(
        tf_replica_specs={
            "PS": V1PodSpec(
                containers=[ps_container],
                restart_policy="Never"
            ),
            "Worker": V1PodSpec(
                containers=[worker_container],
                restart_policy="Never"
            )
        }
    )
)

