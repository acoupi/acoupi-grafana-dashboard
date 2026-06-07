FROM eclipse-mosquitto:2

COPY mosquitto.conf /mosquitto/config/mosquitto.conf
COPY docker-entrypoint.sh /usr/local/bin/acoupi-mosquitto-entrypoint.sh

RUN mkdir -p /mosquitto/config/conf.d
RUN chmod +x /usr/local/bin/acoupi-mosquitto-entrypoint.sh

ENTRYPOINT ["/usr/local/bin/acoupi-mosquitto-entrypoint.sh"]
