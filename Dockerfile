FROM python:3.4
ENV PYTHONUNBUFFERED 1
ENV PYTHONPATH $PYTHONPATH:/code

RUN mkdir /code
RUN mkdir /app

WORKDIR /code
ADD requirements.txt /code/
RUN pip install -r requirements.txt

VOLUME /app

ADD . /code/
ADD ./ui /app/

CMD python3 sigil/server.py runserver