#!/bin/bash -xe
python /app/manage.py migrate --noinput
python /app/manage.py migrate --database mi --noinput
python /app/manage.py migrate_es
# Load initial metadata - ignore errors as we may have already loaded it in to
# this DB
python /app/manage.py loadinitialmetadata || true
# Load initial revisions - ignore errors as we may have already loaded it in to
# this DB
python /app/manage.py loaddata /app/fixtures/test_data.yaml || true
python /app/manage.py createinitialrevisions
python /app/manage.py collectstatic --noinput
# Create superuser - ignore errors as we may have already loaded it in to
# this DB.
if [[ -n "${DJANGO_SUPERUSER_EMAIL}" && -n "${DJANGO_SUPERUSER_PASSWORD}" ]]; then
    python manage.py createsuperuser --noinput || true
fi

# Run runserver in a while loop as the whole docker container will otherwise die
# when there is bad syntax
while true; do
    python /app/manage.py runserver_plus 0.0.0.0:8000
    sleep 1
done
