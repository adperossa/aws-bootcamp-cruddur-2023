FROM python:3.10-slim-buster

WORKDIR /backend-flask

COPY requirements.txt requirements.txt
RUN pip3 install -r requirements.txt
RUN apt-get -y update && apt-get -y install curl

COPY . .

ENV FLASK_ENV=development

EXPOSE ${BACKEND_PORT:-4567}
CMD [ "python3", "-m" , "flask", "run", "--host=0.0.0.0", "--port=4567"]