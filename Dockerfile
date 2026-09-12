FROM python:3.13

RUN apt-get update

WORKDIR /app

COPY requirements.txt .

RUN pip install -r requirements.txt

COPY . /app

CMD ["bash", "start.sh"]

EXPOSE 80
