######################
nginx web server setup
######################

We serve all core4os applications behind a nginx server acting as a proxy and
load balancer.

To support *server-sent-events* (SSE) as well as *web sockets* the nginx
configuration requires several special directives.

This is our ``nginx.conf`` configuration file::

    user www-data;
    worker_processes 4;
    pid /run/nginx.pid;

    events {
        worker_connections 768;
    }

    http {

        server_tokens off;

        include /etc/nginx/mime.types;
        default_type application/octet-stream;

        access_log /var/log/nginx/access.log;
        error_log /var/log/nginx/error.log;

        gzip on;
        gzip_disable "msie6";
        gzip_types *;
        gzip_comp_level 7;
        client_max_body_size 200M;

        map $http_connection $ws_upgrade {
            "upgrade" "WebSocket";
            default "";
        }

        map $http_connection $ws_connection {
            "upgrade" "upgrade";
            default "keep-alive";
        }

        proxy_http_version 1.1;
        proxy_set_header Host $host;
        proxy_set_header X-Forwarded-Proto $scheme;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;

        proxy_set_header Upgrade $ws_upgrade;
        proxy_set_header Connection $ws_connection;

        proxy_connect_timeout 7d;
        proxy_send_timeout 7d;
        proxy_read_timeout 7d;
        keepalive_timeout 3600;

        root /srv/www;

        include /etc/nginx/conf.d/upstream/*.conf;

        server {
            listen 80;
            server_name proxy.aws;

            keepalive_timeout 70;

            include /etc/nginx/conf.d/location/*.conf;

        }
    }

Reading the above configuration you will notice that all *upstreams* and
*location* configuration settings our outsourced in special directories
``./conf.d/upstream`` and ``./conf.d/location``.

Find below the upstream  and location settings for core4os api::

    # content of ./conf.d/upstream/core4api.conf
    upstream core4_api {
        least_conn;server app2.aws:5010;
    }

    # content of ./conf.d/location/core4api.conf
    location /core4 {
        proxy_pass http://core4_api/core4;
    }
    location / {
        proxy_pass http://core4_api/;
    }


..note:: Please note that we handle all our cluster configuration with
         SaltStack. We left out the salt state details for the sake of
         simplicity.
