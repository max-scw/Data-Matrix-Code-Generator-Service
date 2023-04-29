FROM python:3.9.16-slim-bullseye

RUN printf "deb https://deb.debian.org/debian bullseye main\ndeb https://security.debian.org/debian-security bullseye-security main\ndeb https://deb.debian.org/debian bullseye-updates main" > /etc/apt/sources.list

# Install dependencies
RUN apt update && \
    apt install -y apt-transport-https \
				   build-essential \
				   ghostscript && \
    apt clean && \
    rm -rf /var/lib/apt/lists/*

# Install requirements
COPY requirements.txt requirements.txt
RUN pip install -r requirements.txt --no-cache-dir

# Set the working directory
WORKDIR /app

# Copy the app to the container
COPY utils/ utils/
COPY App-Data-Matrix-Generator.py DMCGenerator.py DMCText.py README.md LICENSE ./
COPY config.toml .streamlit/config.toml

# Expose the port
EXPOSE 8501

# Start the app
CMD ["streamlit", "run", "App-Data-Matrix-Generator.py"]