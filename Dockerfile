FROM ubuntu:18.04 as base

COPY . /opt/uwpath.backend
WORKDIR /opt/uwpath.backend

RUN apt update
RUN apt install git ssh -y
RUN apt install wget curl vim libssl-dev ipython -y

FROM base as python38
RUN apt update && apt install python3.8 python3.8-dev python3-pip -y

FROM python38 as uwpath

RUN pip3 install requests && python3.8 deploy/get-poetry.py -y && . ~/.poetry/env && poetry export -f requirements.txt -o requirements.txt
RUN pip3 install -r requirements.txt

ENV PATH /opt/uwpath.backend/:$PATH
EXPOSE 8000
