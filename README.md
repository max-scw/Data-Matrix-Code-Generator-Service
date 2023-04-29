# Data-Matrix-Code-Generator-Service
Python-based functions to build, parse message strings according to the ANSI MH-10 standard and generate a Data-Matrix-Code from it wrapped in a mircoservice for a convenient web-frontend.

## Description
Python-based microservice to generate Data-Matrix-Codes that use ANSI-MH 10 field identifiers (sometimes also referred to as "data identifiers") and a message and format envelopes of ISO / IEC 15434. 

The web-service is build on [streamlit](https://streamlit.io/), which is a python-package for building an interactive website and includes also a web server engine.

## Installation and Usage
The project is ment to be compiled to a Docker container. See Dockerfile for installation instructions.

### manual
Install Python 3.9 (or later) and its package management PIP. Create a virtual environment; then install the requirements to it
```shell
pip install -r requirements.txt
```
Now run [streamlit](https://streamlit.io/)
```shell
streamlit run App-Data-Matrix-Generator.py
```

### Docker
Build docker container based on Python3.9
```shell
docker build --tag=dmc-generator/streamlit .
```
Run container
```shell
docker run -d -p 8502:8501 --name=stramlit-dmc-generator dmc-generator/streamlit
```



## Authors and acknowledgment
max-scw


## License
This project is licensed under the [AGLPv3](https://www.gnu.org/licenses/agpl-3.0.en.html) - see the [LICENSE](LICENSE) file for details.
The python library [treepeom](https://github.com/adamchainz/treepoem), which is used to generate DMCs, uses [ghostscript](https://ghostscript.com/releases/gsdnld.html). The open-source [license of ghostscript](https://ghostscript.com/licensing/index.html) uses a [AGLPv3](https://www.gnu.org/licenses/agpl-3.0.en.html) license (strong copy-left license, i.e. all code in a project that uses ghostscript must be made available as open-source with the same license) but also offers a commercial license. Therefore the project is also bined to AGLPv3 license. 
If there is a way to replace ghostscript, I would be happy to publish the code under a more liberal scheme.

