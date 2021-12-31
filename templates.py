nginx_dir = "/etc/nginx"
backends_dir = nginx_dir + "/svcs"
backends_file=backends_dir + "/svc_{namespace}_{name}_{port}.conf"

servers_dir = nginx_dir + "/servers"
servers_file= servers_dir + "/ingress_{namespace}_{name}.conf"

upstream_template = '''
upstream svc-{namespace}-{svc_name}-{svc_port} {{
{servers}
}}
'''

INVALID_SERVER = "\tserver 0.0.0.1:80;"

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

nginx_conf = '''
user www-data;
worker_processes auto;
pid /run/nginx.pid;

events {{
  worker_connections 768;
}}

http {{
  access_log /var/log/nginx/access.log;
  error_log /var/log/nginx/error.log;

  server {{
  listen 80 default_server;
    server_name _;

    add_header Content-Type text/plain;
    return 200 'nginx default thing';
  }}
  include {backends_dir}/*.conf;
  include {servers_dir}/*.conf;
}}
'''