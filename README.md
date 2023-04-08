# Data-Matrix-Code-Generator-Service
Python-based functions to build, parse message strings according to the ANSI MH-10 standard and generate a Data-Matrix-Code from it wrapped in a mircoservice for a convenient web-frontend.

## Description
Python-based microservice to generate Data-Matrix-Codes that use ANSI-MH 10 field identifiers (sometimes also refered to as "data identifiers") and a message and format envelopes of ISO / IEC 15434. 

## Installation
The project is ment to be compiled to a Docker container. See Dockerfile for installation instructions.

## Usage
### manual
```shell
streamlit run App-Data-Matrix-Generator.py
``

### Docker
```shell
docker build --tag=dmc-generator/streamlit .

docker run -d -p 8501:8501 --name=stramlit-dmc-generator dmc-generator/streamlit
```



## Authors and acknowledgment
max-scw


## License
The code is under MIT License but the python library [treepeom](), which is used to generate DMCs uses [ghostscript](https://ghostscript.com/releases/gsdnld.html). The open-source [license of ghostscript](https://ghostscript.com/licensing/index.html) uses a [AGLPv3](https://www.gnu.org/licenses/agpl-3.0.en.html) license (strong copy-left license, i.e. all code in a project that uses ghostscript must be made available as open-source with the same license) but also offers a commercial license. Therefore the project is also bined to AGLPv3 license.


## status
active
