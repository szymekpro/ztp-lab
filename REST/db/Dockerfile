FROM postgres:16

# Ustawienia domyślne (możesz nadpisać w docker-compose)
ENV POSTGRES_DB=appdb
ENV POSTGRES_USER=appuser
ENV POSTGRES_PASSWORD=apppassword

# Skrypty inicjalizujące (uruchomią się przy 1. starcie, gdy wolumen jest pusty)
COPY ./init/ /docker-entrypoint-initdb.d/

EXPOSE 5432
