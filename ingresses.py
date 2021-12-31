import logging
from kubernetes.client.rest import ApiException
from os import remove

import templates
import utils
import endpoints
import k8sclient as k8s
import nginx

# Essa função recebe um path e transforma em um location pra config do Ingress
# Ela também verifica se o arquivo de endpoint existe, senão cria um vazio.
# Caso contrário o nginx dá erro na hora de subir
def parse_path(path, namespace, name):
    if path.path_type == "Exact":
        path_str = path.path
    elif path.path_type == "Prefix":
        # TODO: This is wrong and not working :)
        path_str = path.path + "*"
    else:
        logging.warning("ingress %s/%s contém path invalido", namespace, name)
        return # Tipo de path não suportado
    if path.backend.service is None or path.backend.service.port.number is None:
       logging.warning("ingress %s/%s não contém um service válido", namespace, name)
       return # Suportamos apenas Ingress com backend.service ou com porta numérica

    try:
        endpoint = k8s.corev1.read_namespaced_endpoints(path.backend.service.name, namespace)
        endpoints.parse_endpoint(endpoint=endpoint, port=path.backend.service.port.number)
    except ApiException as exc:
        if exc.status != 404:
            logging.error("falha ao obter o endpoint: %s", exc.reason)
            return
        logging.warning("endpoint do path %s no ingress %s/%s não existe, usando entrada padrão", path_str, namespace, name)
        upstream_content = templates.upstream_template.format(namespace=namespace, svc_name=path.backend.service.name,svc_port=path.backend.service.port.number, servers=templates.INVALID_SERVER)
        backend_file = templates.backends_file.format(namespace=namespace,name=path.backend.service.name, port=path.backend.service.port.number)
        utils.write_config(filename=backend_file, filecontent=upstream_content)
    new_location = templates.location_template.format(path=path_str, namespace=namespace, svc_name=path.backend.service.name, svc_port=path.backend.service.port.number)
    return new_location

# Essa função recebe um objeto de ingress da fila (watcher) e transforma em uma 
# configuração do tipo "server" pro NGINX
def parse_ingress(ingress):
    try:
        namespace = ingress.metadata.namespace
        name = ingress.metadata.name
        rule = ingress.spec.rules[0] # Suportamos apenas uma rule por enquanto ;)
        paths = rule.http.paths
        template_location = ""
        for path in paths:
            location_config = parse_path(path, namespace, name)
            if location_config is None:
                logging.warning("Pulando path %s devido a configuração invalida", path.path)
                continue

            template_location = template_location + "\n" + location_config            
            new_server = templates.server_template.format(namespace=namespace, name=name, host=rule.host, template_location=template_location)

            svcconfig = templates.servers_file.format(namespace=namespace,name=name)
            utils.write_config(filename=svcconfig, filecontent=new_server)
            nginx.reload_nginx()
    except Exception as e:
        logging.error("falha reconciliando ingress %s/%s: %s", namespace, name, e)

def delete_ingress(ingress):
    try:
        svcconfig = templates.servers_file.format(namespace=ingress.metadata.namespace,name=ingress.metadata.name)
        logging.warning("tentando remover %s", svcconfig)
        remove(svcconfig)
        nginx.reload_nginx()
    except Exception as e:
        logging.error("falha ao remover o arquivo de configuração do ingress %s/%s", ingress.metadata.namespace, ingress.metadata.name)