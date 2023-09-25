FROM qfortier/poetry

EXPOSE 5000

WORKDIR /server
COPY poetry.lock pyproject.toml ./
RUN poetry install

COPY . .

# CMD ["poetry", "run", "celery", "-A", "app.celery", "worker", "-P", "eventlet", "--loglevel=info", "&&", "poetry", "run", "python", "app.py"]
# CMD ["sh", "start.sh"]
CMD ["poetry", "run", "python", "app.py"]
