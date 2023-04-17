# syntax=docker/dockerfile:1

# Base Image
FROM python:3.9.16-bullseye

# Metadata
LABEL author=max-scw
LABEL version=0.1

WORKDIR /app

RUN printf "deb https://deb.debian.org/debian bullseye main \
    deb https://security.debian.org/debian-security bullseye-security main \
    deb https://deb.debian.org/debian bullseye-updates main" > /etc/apt/sources.list

RUN apt install apt-transport-https && \
    apt update && \
# install ghostscript for treepoem
    apt install -y ghostscript

# install necessary python packages
COPY requirements.txt requirements.txt
RUN pip install --no-cache-dir --upgrade -r requirements.txt

# programm code
COPY utils utils/
COPY ["App-Data-Matrix-Generator.py", "DMCGenerator.py", "DMCText.py", "README.md", "LICENSE", "./"]

# theme / style settings
COPY config.toml .streamlit/config.toml

EXPOSE 8501
HEALTHCHECK CMD curl --fail http://localhost:8501/_stcore/health
ENTRYPOINT ["streamlit", "run", "App-Data-Matrix-Generator.py", "--server.port=8501", "--server.address=0.0.0.0"]

