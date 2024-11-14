psql -d
dropdb aplat1
createdb aplat1
flask fab create-db
flask fab create-admin
flask run --host 0.0.0.0 --port 5000 --with-threads --reload
