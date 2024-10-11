FROM python:3

COPY requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt

# Set Workdir
WORKDIR /usr/src/app

# Mount points sourcedir
VOLUME	["/usr/src/app"]

# Start service
# Run app.py when the container launches
EXPOSE 8080
CMD gunicorn --access-logfile - -b 0.0.0.0:8080 app:app --reload