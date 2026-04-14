FROM python:3.11-slim

RUN useradd -m -s /bin/bash sandboxuser

# Install ONLY the allowed packages
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

RUN mkdir /charts /data /code && \
    chown -R sandboxuser:sandboxuser /charts /data /code

# Switch to non-root user
USER sandboxuser
WORKDIR /code

# The python script will be mounted here and executed
CMD ["python", "script.py"]