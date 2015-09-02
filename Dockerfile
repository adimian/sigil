FROM python:3.4
ENV PYTHONUNBUFFERED 1
ENV PYTHONPATH $PYTHONPATH:/code
RUN mkdir /code
WORKDIR /code
ADD requirements.txt /code/
RUN pip install -r requirements.txt

VOLUME /code

ADD . /code/
CMD python3 sigil/server.py runserver