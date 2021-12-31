from kubernetes import client, config, watch
import os

def init():
    if os.path.isfile("/var/run/secrets/kubernetes.io/serviceaccount/token"):
        config.load_incluster_config()
    else:
        config.load_kube_config()
    
    global networkingv1
    global corev1
    global w
    networkingv1 = client.NetworkingV1Api()
    corev1 = client.CoreV1Api()
    w = watch.Watch()