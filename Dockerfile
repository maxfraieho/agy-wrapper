FROM vanjayak/open-design:latest
USER root
COPY agy /usr/local/bin/agy
RUN chmod +x /usr/local/bin/agy
USER open-design
