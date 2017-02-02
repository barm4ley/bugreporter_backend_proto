FROM python:3.5-slim

MAINTAINER Max Musich <maxim@unity3d.com>

ENV PIP_GLOBAL_OPTS "-vvv --no-cache-dir"

RUN apt-get update \
 && apt-get install -y vim \
 && apt-get install -y net-tools

RUN pip3 $PIP_GLOBAL_OPTS install --upgrade pip \
                                           flask \
                                           requests \
                                           jsonpickle \
                                           redis

ADD app /app

EXPOSE 8080

CMD ["/app/server.py"]
