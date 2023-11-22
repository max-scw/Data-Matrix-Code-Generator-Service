FROM python:3.9.16-slim-bullseye
ENV PYTHONUNBUFFERED 1

# Metadata
LABEL author=SCW-MAX
LABEL version=2023.08

# Environment variables (default values)
ENV LOGFILE=data-matrix-generator-streamlit


RUN printf "deb https://deb.debian.org/debian bullseye main \
    deb https://security.debian.org/debian-security bullseye-security main \
    deb https://deb.debian.org/debian bullseye-updates main" > /etc/apt/sources.list


# Install dependencies
RUN apt update && \
    apt install -y apt-transport-https \
				   build-essential \
				   ghostscript && \
    apt clean && \
    rm -rf /var/lib/apt/lists/* 

# new default user
RUN useradd -ms /bin/bash appuser
USER appuser
# Set the working directory
WORKDIR /home/appuser

# configure python & pip
RUN pip3 install --no-cache-dir --upgrade \
    pip \
    virtualenv

# create virtual environment
RUN python3 -m venv venv
# put venv on the first position of PATH, because normal "activation" only affects the single RUN command in a Dockerfile
ENV PATH="/home/appuser/venv/bin:$PATH"
RUN pip install --upgrade pip

# Install requirements
COPY app-requirements.txt requirements.txt
RUN pip install -r requirements.txt --no-cache-dir

RUN mkdir source/
WORKDIR /home/appuser/source

# Copy the app to the container
COPY DataMatrixCode/ ./DataMatrixCode/
COPY app-main.py utils.py README.md LICENSE ./

USER root
RUN chown -R appuser:appuser /home/appuser
USER appuser

# Expose the ports
EXPOSE 8501

HEALTHCHECK CMD curl --fail http://localhost:8501/_stcore/health

# Start the app
ENTRYPOINT ["streamlit", "run", "app-main.py", "--server.port=8501", "--server.address=0.0.0.0"]
# ENTRYPOINT ["tail", "-f", "/dev/null"]