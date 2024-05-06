# syntax=docker/dockerfile:1

# Base Image
FROM python:3.11.9-alpine

# Metadata
LABEL author=SCW-MAX
LABEL version=2024.05

# Environment variables (default values)
ENV LOGFILE=data-matrix-generator-fastapi


WORKDIR /app

# install ghostscript for treepoem
RUN apk update && \
	apk add ghostscript

# install necessary python packages
COPY api-requirements.txt requirements.txt
RUN pip install --no-cache-dir --upgrade -r requirements.txt

# programm code
COPY DataMatrixCode/ ./DataMatrixCode/
COPY api-main.py api-logging-config.yml README.md LICENSE ./


# Expose the port
EXPOSE 8000
	
CMD ["uvicorn", "api-main:api", "--host=0.0.0.0", "--port=8000", "--log-config", "api-logging-config.yml"]

