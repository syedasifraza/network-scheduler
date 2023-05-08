FROM python:3.7
RUN pip install kubernetes
COPY config /config
COPY scheduler.py /scheduler.py
CMD python /scheduler.py
