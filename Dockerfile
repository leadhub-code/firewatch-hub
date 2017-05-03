FROM debian:jessie

MAINTAINER Petr Messner

ENV DEBIAN_FRONTEND noninteractive
ENV PYTHONUNBUFFERED 1

RUN apt-get update
RUN apt-get install -y --no-install-recommends \
    python3-venv python3-dev gcc

RUN python3 -m venv /venv
RUN /venv/bin/pip install -U pip
RUN /venv/bin/pip install gunicorn

COPY requirements.txt /app/requirements.txt
RUN /venv/bin/pip install -r /app/requirements.txt

COPY . /app

RUN /venv/bin/pip install /app

#RUN sed -i 's/raise InsecureTransportError()/raise InsecureTransportError(str(locals()))/g' /venv/lib/python3.4/site-packages/oauthlib/oauth2/rfc6749/parameters.py

RUN groupadd -g 500 app && \
    useradd --no-create-home -u 500 -g 500 app

USER app

CMD [ \
    "/venv/bin/gunicorn", \
    "--workers", "2", \
    "--bind", "0.0.0.0:8000", \
    "--max-requests", "1000", \
    "--forwarded-allow-ips=172.17.0.1,192.168.122.1", \
    "firewatch_hub:get_app('/conf/firewatch-hub.yaml')" \
]
