# syntax=docker/dockerfile:1

# Base Image
FROM python:3.9.16-alpine

# Metadata
LABEL author=SCW-MAX
LABEL version=2023.08

# Environment variables (default values)
ENV LOGFILE=data-matrix-generator-fastapi


WORKDIR /app

# install ghostscript for treepoem
RUN apk update && \
	apk add ghostscript

# install necessary python packages
COPY api.requirements.txt requirements.txt
RUN pip install --no-cache-dir --upgrade -r requirements.txt

# programm code
COPY DataMatrixCode/ ./
COPY .api-main.py api-logging_config.yml README.md LICENSE ./


# Expose the port
EXPOSE 5000
	
CMD ["uvicorn", "api-main:app", "--host=0.0.0.0", "--port=5000", "--log-config", "api-logging_config.yml"]

