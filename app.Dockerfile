FROM python:3.9.16-slim-bullseye as compiler
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
# RUN mkdir .streamlit
COPY .streamlit/config.toml .streamlit/config.toml




# FROM python:3.9.16-slim-bullseye as runner
# # # new default user
# # RUN useradd -ms /bin/bash appuser
# # USER appuser
# # Set the working directory
# WORKDIR /home/appuser

# # copy virtual environment
# COPY --from=compiler /home/appuser/venv/ ./venv/
# # put venv first to mimic activation
# ENV PATH="/home/appuser/venv/bin:$PATH"

# # copy ghostscript 
# COPY --from=compiler /usr/bin/gs /usr/bin/gs
# COPY --from=compiler /usr/share/ghostscript/ /usr/share/ghostscript/
# COPY --from=compiler /usr/share/color/icc/ghostscript/ /usr/share/color/icc/ghostscript/
# COPY --from=compiler /var/lib/ghostscript/ /var/lib/ghostscript/
# COPY --from=compiler /etc/ghostscript /etc/ghostscript
# COPY --from=compiler /usr/lib/x86_64-linux-gnu/ /usr/lib/x86_64-linux-gnu/
# COPY --from=compiler /lib/x86_64-linux-gnu/ /lib/x86_64-linux-gnu/


# # copy source code
# COPY --from=compiler /home/appuser/source .


# # gs -dSAFER -dNOPAUSE -dBATCH -sDEVICE=bbox -c <</PageOffset [3000 3000]>> setpagedevice -f -


# Expose the ports
EXPOSE 8501

# Start the app
CMD ["streamlit", "run", "app-main.py"]
#ENTRYPOINT ["tail", "-f", "/dev/null"]