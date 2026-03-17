FROM postgres:16

# Skrypty inicjalizujące (uruchomią się przy 1. starcie, gdy wolumen jest pusty)
COPY ./app/REST/db/init/ /docker-entrypoint-initdb.d/

EXPOSE 5432
