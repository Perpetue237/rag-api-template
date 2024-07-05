FROM pytorch/pytorch:2.0.1-cuda11.7-cudnn8-devel

ENV USERNAME="$USERNAME"
ARG DEBIAN_FRONTEND=noninteractive
ENV TZ Europe/Berlin

RUN echo $USERNAME

RUN apt-get -y update
RUN apt-get -y install git curl
RUN curl -fsSL https://deb.nodesource.com/setup_lts.x | bash -
RUN apt-get install -y nodejs
RUN apt-get install -y tree


COPY . .

RUN  pip3 --no-cache-dir install -r requirements.txt 
