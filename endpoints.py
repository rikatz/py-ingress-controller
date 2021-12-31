import logging
import os

# Imports locais
import utils
import templates
import nginx

# Recebe um objeto Endpoint e escreve o arquivo dele. Pode ser usado tanto no "watcher" quanto pelo 
# controller de objetos de ingress
def parse_endpoint(endpoint, port):
    if endpoint.kind == "Endpoints":
        try:
            namespace = endpoint.metadata.namespace
            name = endpoint.metadata.name
            subsets = endpoint.subsets
            backend_file = ""

            logging.debug("recebi o endpoint %s/%s", namespace, name)

            # Se não recebeu porta, veio do watcher de endpoints então precisamos descobrir se o arquivo
            # dumb já existe.
            if port == -1:
                if not subsets:
                     logging.debug("endpoint %s/%s não contém endereços, pulando", namespace, name)
                     return
                for subset in subsets:
                    for ports in subset.ports:
                        if os.path.isfile(templates.backends_file.format(namespace=namespace,name=name, port=ports.port)):
                            port = ports.port
                            backend_file = templates.backends_file.format(namespace=namespace,name=name, port=port)
                            break
            else:    
                backend_file = templates.backends_file.format(namespace=namespace,name=name, port=port)

            if backend_file == "":
                 logging.warning("Endpoint %s/%s não usado por nenhum Ingress, pulando", namespace, name)
                 return

            for subset in subsets:
              addresses = subset.addresses
              servers = ""
              # Pegamos todos os endereços dos Endpoints
              for address in addresses:
                  servers +=  "\tserver " + address.ip + ":" + str(port) + ";\n"
              for ports in subset.ports:
                 if ports.port == port:
                   upstream_file = templates.upstream_template.format(namespace=namespace, svc_name=name, svc_port=port, servers=servers)
                   utils.write_config(filename=backend_file, filecontent=upstream_file)
                   break

        except Exception as e:
            logging.error("falha ao reconciliar endpoint %s/%s: %s", namespace, name, e)