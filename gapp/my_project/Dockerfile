```Dockerfile
# Use the official lightweight Python runtime as a parent image from Debian Buster (stable)
FROM python:3.9-slim-buster

# Set environment variables to ensure consistent behavior across different systems.
ENV PYTHONUNBUFFERED 1 \
    APP_ENV=production \



# Create and set working directory for all subsequent instructions
WORKDIR /app


# Install system dependencies required by the application (e.g., build tools, libraries)
RUN apt-get update && apt-get install -y --no-install-recommends \
        gcc \
        libc6-dev \
    && rm -rf /var/lib/apt/lists/*



# Copy just what's needed to avoid invalidating cache layers later on
COPY requirements.txt .

# Install Python dependencies defined in 'requirements.txt'
RUN pip install --upgrade pip \ 
  && pip install --no-cache-dir -r requirements.txt


WORKDIR /app/src

# Assuming the project has an entry file named `main.py`
# Copying all files from my_project to current directory
COPY . .

# Expose port if your application listens on a specific one (e.g., Flask default 5000)
EXPOSE $APP_PORT


# Define command or script that will run when starting this container.
CMD ["python", "app/main.py"]

```

### Explanation:

1. **Base Image**: We start with `python:3.9-slim-buster` to get a minimal Python environment, which is ideal for production deployments.

2. **Environment Variables**:
    - Set `PYTHONUNBUFFERED=1`: This ensures that the output from running your app isn't buffered by default.
    - The custom variable `APP_ENV=production` can be used in application code if needed to differentiate between development and other environments (though not strictly necessary for Docker).

3. **Working Directory**: We set `/app` as our working directory, which simplifies later commands.

4. **System Dependencies Installation**:
   These are crucial but kept minimal by using `--no-install-recommends`. This reduces the image size without compromising functionality.
   
5. **Copy Requirements and Install Python Packages**:
    - Copying only what is necessary to avoid invalidating Docker layers unnecessarily (only requirements.txt initially).
    
6. **Setting Source Code Directory & Copying Files into App Context**: The working directory inside `/app/src` now contains the application's source code.

7. **Expose Port**: Assumes your app uses a specific port; replace `$APP_PORT` with an actual number if needed or remove this line.
   
8. **Default Command to Run Application**:
    - `CMD ["python", "app/main.py"]`: Starts up the Python application defined in 'main.py'. Replace as necessary for different applications.

### Best Practices Followed:

- Using a minimal base image (`slim-buster`).
- Setting environment variables.
- Keeping unnecessary files out of Docker layers (use .dockerignore to ignore non-essential files/directories like temporary directories, IDE configs etc.).
- Copying requirements.txt separately before copying the rest allows better caching and faster builds during development.

### Note:

Make sure your application's entry point (`app/main.py`) or command in `CMD` is correctly specified. Adjust paths if necessary depending on how you're structuring project files inside `/my_project`.