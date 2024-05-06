FROM python:3.11.9-slim-bullseye
ENV PYTHONUNBUFFERED 1

# Metadata
LABEL author=SCW-MAX
LABEL version=2024.05

# Environment variables (default values)
ENV LOGFILE=data-matrix-generator-streamlit


RUN printf "deb https://deb.debian.org/debian bullseye main \
    deb https://security.debian.org/debian-security bullseye-security main \
    deb https://deb.debian.org/debian bullseye-updates main" > /etc/apt/sources.list


# Install dependencies
RUN apt update && \
    apt install -y apt-transport-https \
				   build-essential \
				   ghostscript \
                   curl && \
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
COPY app-generator.requirements.txt requirements.txt
RUN pip install -r requirements.txt --no-cache-dir

RUN mkdir source/
WORKDIR /home/appuser/source

# Copy the app to the container
COPY DataMatrixCode/ ./DataMatrixCode/
COPY utils/ ./utils
COPY app-generator.py default_config.toml README.md LICENSE ./

USER root
RUN chown -R appuser:appuser /home/appuser
USER appuser

# Expose the ports
EXPOSE 8501

# Define the health check using curl for both HTTP and HTTPS
HEALTHCHECK --interval=30s --timeout=5s \
  CMD (curl -fsk http://localhost:8501/_stcore/health) || (curl -fsk https://localhost:8501/_stcore/health) || exit 1

# Start the app
ENTRYPOINT ["streamlit", "run", "app-generator.py", "--server.port=8501", "--server.address=0.0.0.0"]
# ENTRYPOINT ["tail", "-f", "/dev/null"]
