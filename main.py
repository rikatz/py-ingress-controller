from concurrent.futures import ThreadPoolExecutor, as_completed

import endpoints
import ingresses
import k8sclient as k8s
import nginx
import logging

logging.basicConfig(
    format="%(asctime)s:%(levelname)s:%(message)s", datefmt="%d/%m/%Y %H:%M:%S"
)
logging.getLogger().setLevel(logging.INFO)

k8s.init()
nginx.initialize_nginx()
# Função para receber os objetos de ingress e tratar
def watch_ingress(k8sobject): 
    stream = k8s.w.stream(k8sobject)
    for event in stream:
        if event['type'] != "DELETED":
            logging.warning("Reconciliando o Ingress %s/%s", event['object'].metadata.namespace, event['object'].metadata.name)
            ingress = k8s.networkingv1.read_namespaced_ingress(event['object'].metadata.name, event['object'].metadata.namespace)
            ingresses.parse_ingress(ingress)
        else:
            logging.warning("Removendo o ingress %s/%s", event['object'].metadata.namespace, event['object'].metadata.name)
            ingresses.delete_ingress(ingress)

# Função para receber os objetos de endpoints e tratar
def watch_endpoints(k8sobject): 
    stream = k8s.w.stream(k8sobject)
    for event in stream:
        if event['type'] != "DELETED":
            logging.debug("Reconciliando o Endpoint %s/%s", event['object'].metadata.namespace, event['object'].metadata.name)
            endpoint = k8s.corev1.read_namespaced_endpoints(event['object'].metadata.name, event['object'].metadata.namespace)
            endpoints.parse_endpoint(endpoint, -1)
        else:
            # TODO: Implementar
            # TODO2: Implementar quando um endpoint existe mas rola scale==0 (sem subsets)
            logging.warning("Delete não foi implementado")


futures = []

# Fábrica de salsicha...entra objeto do Kubernetes, sai configuração do NGINX
# Por sinal eu to fazendo alguma cagada aqui que os erros estão travando as threads :D
# Então, vamos tentar resolver isso aqui como um TODO:
with ThreadPoolExecutor(max_workers=10) as executor:
    futures.append(executor.submit(watch_ingress, k8s.networkingv1.list_ingress_for_all_namespaces))
    futures.append(executor.submit(watch_endpoints, k8s.corev1.list_endpoints_for_all_namespaces))
    exceptions = []
    for future in as_completed(futures):
        res = future.exception()	# future.exception() get exception
        exceptions.append(res)

    print(exceptions)

