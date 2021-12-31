from kubernetes import client, config, watch

def init():
    config.load_kube_config()
    global networkingv1
    global corev1
    global w
    networkingv1 = client.NetworkingV1Api()
    corev1 = client.CoreV1Api()
    w = watch.Watch()