from kubernetes import client, config, watch
from concurrent.futures import ThreadPoolExecutor, as_completed
from threading import Lock
import os

import logging
logging.basicConfig(
    format="%(asctime)s:%(levelname)s:%(message)s", datefmt="%d/%m/%Y %H:%M:%S"
)
logging.getLogger().setLevel(logging.INFO)

# Paths
# TODO: Transformar em configurável pelo programa
servers_dir="/tmp/servers/"
backends_file="/tmp/svcs/svc_{namespace}_{name}_{port}.conf"

# Kubernetes Stuff
config.load_kube_config()
networkingv1 = client.NetworkingV1Api()
corev1 = client.CoreV1Api()
w = watch.Watch()
g_Lock = Lock() 

### Templates:
server_template = '''
      ## ingress_{namespace}_{name}.conf
      server {{
         listen       80;
         server_name {host};
         root         /usr/share/nginx/html/;
{template_location}
      }}
     '''

location_template = '''
         location {path} {{
            proxy_set_header Host $host;
            proxy_set_header X-Real-IP $remote_addr;
            proxy_pass http://svc-{namespace}-{svc_name}-{svc_port};
         }}
'''

upstream_template = '''
upstream svc-{namespace}-{svc_name}-{svc_port} {{
        {servers}
}}
'''
# Essa função recebe um path e transforma em um location pra config do Ingress
# Ela também verifica se o arquivo de endpoint existe, senão cria um vazio.
# Caso contrário o nginx dá erro na hora de subir
def parse_path(path, namespace):
    if path.path_type == "Exact":
        path_str = path.path
    elif path.path_type == "Prefix":
        path_str = path.path + "*"
    else:
        return # Tipo de path não suportado
    
    if path.backend.service is None:
       return # Suportamos apenas Ingress com backend.service
    if path.backend.service.port.number is None:
       return # Suportamos apenas backends com porta numérica
  
    # Se o arquivo não existe a gente cria!
    backend_file = backends_file.format(namespace=namespace,name=path.backend.service.name, port=path.backend.service.port.number)
    if not os.path.isfile(backend_file):
        server = "non-existent-server;"
        upstream_file = upstream_template.format(namespace=namespace, svc_name=path.backend.service.name, svc_port=path.backend.service.port.number, servers=server)
        with g_Lock: # Tipo um mutex, para evitar race condition na hora de escrever arquivos
            f = open(backend_file, "w")
            f.write(upstream_file)
            f.close()
    
    new_location = location_template.format(path=path_str, namespace=namespace, svc_name=path.backend.service.name, svc_port=path.backend.service.port.number)
    return new_location

# Essa função recebe um objeto de ingress da fila (watcher) e transforma em uma 
# configuração do tipo "server" pro NGINX
def parse_ingress(ingress):
    namespace = ingress.metadata.namespace
    name = ingress.metadata.name
    rule = ingress.spec.rules[0] # Suportamos apenas uma rule por enquanto ;)
    paths = rule.http.paths
    template_location = ""
    for path in paths:
        location_config = parse_path(path, namespace)
        if not location_config is None:
            template_location = template_location + "\n" + location_config
        else:
            logging.warn("Skipping path %s due to invalid configuration", path.path)
  
    new_server = server_template.format(namespace=namespace, name=name, host=rule.host, template_location=template_location)
    print(new_server) 

# TODO: Implementar.
# Recebe um objeto Endpoint, vê se ele pertence a algum objeto de Ingress (vai ficar lento...)
# E se pertencer implementa a reescrita do arquivo de balancers
def parse_endpoint(endpoint):
    if endpoint.kind == "Endpoints":
       print("Hello Endpoint %s", str(endpoint))
    else:
        print("bla")

# Função para receber os objetos de ingress e tratar
def watch_ingress(k8sobject): 
    stream = w.stream(k8sobject)
    for event in stream:
        logging.info("Reconciliando o Ingress %s/%s", event['object'].metadata.namespace, event['object'].metadata.name)
        ingress = networkingv1.read_namespaced_ingress(event['object'].metadata.name, event['object'].metadata.namespace)
        parse_ingress(ingress)

# Função para receber os objetos de endpoints e tratar
def watch_endpoints(k8sobject): 
    stream = w.stream(k8sobject)
    for event in stream:
        logging.info("Reconciliando o Ingress %s/%s", event['object'].metadata.namespace, event['object'].metadata.name)
        endpoint = corev1.read_namespaced_endpoints(event['object'].metadata.name, event['object'].metadata.namespace)
        parse_endpoint(endpoint)

futures = []

# Fábrica de salsicha...entra objeto do Kubernetes, sai configuração do NGINX
with ThreadPoolExecutor(max_workers=10) as executor:
    futures.append(executor.submit(watch_ingress, networkingv1.list_ingress_for_all_namespaces))
    #futures.append(executor.submit(watch_endpoints, corev1.list_endpoints_for_all_namespaces))
    exceptions = []
    for future in as_completed(futures):
        res = future.exception()	# future.exception() get exception
        exceptions.append(res)

    print(exceptions)

