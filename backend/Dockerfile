FROM python:3.12

WORKDIR /app

COPY requirements/ /app/requirements/

RUN pip install --no-cache-dir --upgrade -r /app/requirements/backend.txt

COPY core/ /app/core
COPY backend/ /app/backend
COPY alembic/ /app/alembic
COPY alembic.ini /app/alembic.ini
COPY scripts/ /app/scripts

RUN chmod +x /app/scripts/*

CMD ["/app/scripts/be-start.sh"]