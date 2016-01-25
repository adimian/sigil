FROM python:3.4
ENV PYTHONUNBUFFERED 1
ENV PYTHONPATH $PYTHONPATH:/sigil

RUN mkdir /sigil
VOLUME /sigil

WORKDIR /sigil
ADD requirements.txt /sigil/
RUN pip install -U pip && pip install -r requirements.txt

ADD . /sigil/
ADD sigil_cmd /usr/local/bin/sigil
RUN chmod +x /usr/local/bin/sigil

CMD sigil runserver