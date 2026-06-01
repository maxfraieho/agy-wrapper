FROM vanjayak/open-design:latest
USER root
RUN apk add --no-cache python3
COPY agy /usr/local/bin/agy
COPY server.py /usr/local/bin/agy-server
RUN chmod +x /usr/local/bin/agy /usr/local/bin/agy-server
USER open-design
