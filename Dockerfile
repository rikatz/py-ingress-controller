FROM python:3-slim

WORKDIR /usr/src/app

RUN apt-get -y update && apt-get -y dist-upgrade \
    && apt-get --no-install-recommends -y install nginx && apt clean all \
    && mkdir -p /etc/nginx/svcs /etc/nginx/servers

COPY requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

CMD [ "python", "./main.py" ]
