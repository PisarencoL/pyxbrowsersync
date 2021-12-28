# Copyright (c) 2021 Lucia Pisarenco, Berlin, Germany
FROM python:3.9-slim

RUN mkdir /xbrowsersync
COPY app /xbrowsersync/app/
COPY requirements.txt gunicorn.conf.py /xbrowsersync/
WORKDIR /xbrowsersync
RUN pip install -r requirements.txt

ENTRYPOINT ["gunicorn"]
CMD ["-w", "4", "-b", "0:5000", "--forwarded-allow-ips", "*", "app.app:app"]
