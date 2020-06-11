FROM python:3.8.3-buster

LABEL maintainer "Dallas Fraser <dallas.fraser.waterloo@gmail.com>"

RUN mkdir /mlsb-bot

WORKDIR /mlsb-bot

COPY . /mlsb-bot

RUN pip install --no-cache-dir -r requirements.txt

ENV FLASK_ENV="docker"

EXPOSE 5001