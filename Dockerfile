FROM python:3.4
ENV PYTHONUNBUFFERED 1
ENV PYTHONPATH $PYTHONPATH:/sigil

RUN mkdir /sigil
VOLUME /sigil

WORKDIR /sigil
ADD requirements.txt /sigil/
RUN pip install -U pip && pip install -r requirements.txt

ADD . /sigil/

CMD python3 sigil/server.py runserver