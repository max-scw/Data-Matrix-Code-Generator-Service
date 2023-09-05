FROM python:3.9.16-slim-bullseye

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
    rm -rf /var/lib/apt/lists/* \

# new default user
USER appuser
# Set the working directory
WORKDIR /home/appuser

# configure python & pip
RUN pip3 install --no-cache-dir --upgrade \
    pip \
    virtualenv

ENV VIRTUAL_ENV=/home/appuser/venv
RUN virtualenv ${VIRTUAL_ENV}
RUN . ${VIRTUAL_ENV}/bin/activate


# Install requirements
COPY app-requirements.txt requirements.txt
RUN pip install -r requirements.txt --no-cache-dir


# Copy the app to the container
COPY DataMatrixCode/ ./DataMatrixCode/
COPY app-main.py utils.py README.md LICENSE ./
RUN mkdir .streamlit
COPY .streamlit/config.toml .streamlit/config.toml

# Expose the port
EXPOSE 8501

# Start the app
CMD ["streamlit", "run", "app-main.py"]