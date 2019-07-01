FROM python:3.7

RUN pip install requirements.txt

RUN mkdir /app
ADD . /app
WORKDIR /app

CMD python /app/teleg_bot.py
