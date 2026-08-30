FROM python:3.12

WORKDIR /app

COPY requirements/ /app/requirements/

RUN pip install --no-cache-dir --upgrade -r /app/requirements/backend.txt

COPY . /app

RUN chmod +x /app/scripts/*

CMD ["/app/scripts/be-start.sh"]
