FROM caddy:2

RUN apk add --no-cache gettext

COPY Caddyfile.template /etc/caddy/Caddyfile.template
COPY docker-entrypoint.sh /usr/local/bin/acoupi-caddy-entrypoint.sh

RUN chmod +x /usr/local/bin/acoupi-caddy-entrypoint.sh

ENTRYPOINT ["/usr/local/bin/acoupi-caddy-entrypoint.sh"]
