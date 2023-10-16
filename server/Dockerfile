FROM python:3.11-buster 

RUN pip install poetry==1.6.1

ENV POETRY_NO_INTERACTION=1 \
    POETRY_VIRTUALENVS_IN_PROJECT=1 \
    POETRY_VIRTUALENVS_CREATE=1 \
    POETRY_CACHE_DIR=/tmp/poetry_cache

WORKDIR /app

COPY pyproject.toml poetry.lock ./

RUN --mount=type=cache,target=$POETRY_CACHE_DIR poetry install --without dev --no-root

EXPOSE 5002

COPY . .

# RUN mkdir -p /usr/share/fonts &&\
#     unzip ./Noto_Sans_Mono.zip -d /usr/share/fonts

# CMD ["poetry", "run", "celery", "-A", "app.celery", "worker", "-P", "eventlet", "--loglevel=info", "&&", "poetry", "run", "python", "app.py"]
CMD ["sh", "start.sh"]
# CMD ["poetry", "run", "python", "app.py"]
