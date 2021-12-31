import os
import sys
import logging
import subprocess

import templates
import utils

NGINX="/usr/sbin/nginx"

def initialize_nginx():
    if not os.path.isdir(templates.servers_dir) or not os.path.isdir(templates.backends_dir) or not os.path.isdir(templates.nginx_dir):
        logging.fatal("os diretórios %s, %s e %s devem existir", templates.nginx_dir, templates.servers_dir, templates.backends_dir)
        sys.exit(1)
    
    if not os.access(templates.backends_dir, os.W_OK) or not os.access(templates.servers_dir, os.W_OK) or not os.access(templates.nginx_dir, os.W_OK):
        logging.fatal("o usuário executando o programa deve possuir permissão de escrita em %s, %s e %s", templates.nginx_dir, templates.servers_dir, templates.backends_dir)
        sys.exit(1)

    nginx_config = templates.nginx_conf.format(backends_dir=templates.backends_dir, servers_dir=templates.servers_dir)
    nginx_conf_file = templates.nginx_dir + "/nginx.conf"
    utils.write_config(nginx_conf_file, nginx_config)
    if os.path.isfile("/run/nginx.pid"):
            try:
                subprocess.run([NGINX, "-s", "stop"], check=True)
            except:
                logging.fatal("falha ao parar a instância em execução do NGINX")
                sys.exit(1)      
    
    try:
        subprocess.run([NGINX], check=True)
    except:
        logging.fatal("falha ao iniciar o NGINX")
        sys.exit(1)

def reload_nginx():
    try:
        subprocess.run([NGINX, "-t"], check=True)
        subprocess.run([NGINX, "-s", "reload"])
    except:
        logging.error("falha ao recarregar instância em execução")