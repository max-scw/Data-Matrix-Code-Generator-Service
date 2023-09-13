# Data-Matrix-Code-Generator-Service
Python-based functions to build and parse message strings according to the ANSI MH-10 standard and generate a Data-Matrix-Code from it wrapped in a mirco-service for a convenient web-frontend.

(Other standards may be implemented later.)

There are three options:

- **vanilla package/code**: The python package [DataMatrixCode](/DataMatrixcode) includes the code to build, parse, generate DMCs (using the [treepeom](https://github.com/adamchainz/treepoem) package)
- **api**: A [fastAPI](https://fastapi.tiangolo.com/)-based web-service that wraps the DataMatrixCode package to a minimal web-api
- **app** (with convenient GUI front-end): This web-service is build on [streamlit](https://streamlit.io/), which is a python-package for building an interactive website and includes also a web server engine.

## Installation and Usage

### Installation
The project is meant to be compiled to its Docker containers. See Dockerfile for installation instructions.

#### local
Install Python 3.9 (or later) and its package management PIP. Create a virtual environment; then install the requirements to it
```shell
pip install -r api.requirements.txt
pip install -r app.requirements.txt

```
Now run [fastAPI](https://fastapi.tiangolo.com/) and / or [streamlit](https://streamlit.io/):
```shell
uvicorn api-main:api
streamlit run app-main.py
```
You can access the services now in your webbrowser on the default ports: http://localhost:8000 and http://localhost:8501 for the api and the app respectively

#### Docker
Build docker container based on Python3.9
```shell
docker build --tag=dmc-generator-api -f api.Dockerfile .
docker build --tag=dmc-generator-app -f app.Dockerfile .
```
Run containers
```shell
docker run -d -p 5001:8000 --name=fastapi-dmc-generator dmc-generator-api
docker run -d -p 5002:8501 --name=streamlit-dmc-generator dmc-generator-app
```
Where you can now access the services on: http://localhost:5001 and http://localhost:5002.
### Customize

One can set all options also as environment variables with the prefix `DMC_` ,e.g.:
```shell
docker run -d -p 5002:8501 --name=streamlit-dmc-generator -e DMC_TITLE="My Data-Matrix-Generator" -e DMC_NUMBER_OF_QUIET_ZONE_MODULES=10 dmc-generator-app
```
(Options are the same as in the *config.toml*-file but with the prefix `DMC_` and an underscore `_` before capital letters as all environment variables should be capital letters only, e.g. `NumberOfQuietZoneModules` in *config.toml* => `DMC_NUMBER_QUIET_ZONE_MODULES` as enviroment variable.)

You may also want to adjust the text on the top of the page with the keywords `Title`, `Header`, `Subheader`, and `Text` (in descending font) in the *config.toml*-file or `DMC_TITLE`, `DMC_HEADER`, `DMC_SUBHEADER`, and `DMC_TEXT` respectively as environment vairalbes.


### Usage

#### [streamlit](https://streamlit.io/)-based web-app
##### Interface
The initial page shows only the required fields, if any are specified. If not, the initial page consists of a single row (data identifier as drop down menu + input field).

![initial view](docs/app/DMC_Home.jpg)

Note that you can change the options dynamically when expanding the container "options". The options are stored for the session. The default options can be specified for in the configuration file when starting the streamlit server (for examples see below.)

![expanded options](docs/app/DMC_options.jpg)

When selecting a new data identifier, the corresponding explanation is displayed above the row:

![explain DI](docs/app/DMC_explanation.jpg)

and a warning is issued when the input does not comply with the expected format.

![warning](docs/app/DMC_warning_comply.jpg)

For generating a code simply click the button "generate". A correct message string is created automatically and the number of ASCII characters of this string is displayed next to the image of the code. 

![generated DMC](docs/app/DMC_generate.jpg)

Note that no DMC is generated if one leaves one of the required fields empty.

![error missing required field](docs/app/DMC_error_missing_field.jpg)


##### Configuration
[streamlit](https://streamlit.io/) can be configured via a TOML file [config.toml](config.toml), e.g. the `primarycolor` of the overall theme (see config file as example or the streamlit-docs).
We extended this file to add a section `[DMC]`, where one can specify field identifiers that should be required in the code. This is an array of strings. One can connect two identifiers as OR with an | symbol. See example.

```TOML
[DMC]
requiredDataIdentifiers = ["P", "S|T", "V"]
```
You can specify the default option values with the following keys (this are the default values, which do not have to be explicitly specified.)
```TOML
[DMC]
UseMessageEnvelope = true
UseFormatEnvelope = true
RectangularDMC = false
NumberOfQuietZoneModuls = 2
ExplainDataIdentifiers = true
````






#### [fastapi](https://fastapi.tiangolo.com/)-based web-api
fastapi conveniently builds an automatic documentation at the `/docs` endpoint. Please check these examples there.

![initial view](docs/api/DMC_fastapi_docs.jpg)


## Authors and acknowledgment
max-scw


## License
This project is licensed under the [AGLPv3](https://www.gnu.org/licenses/agpl-3.0.en.html) - see the [LICENSE](LICENSE) file for details.

The python library [treepeom](https://github.com/adamchainz/treepoem), which is used to generate DMCs, uses [ghostscript](https://ghostscript.com/releases/gsdnld.html). The open-source [license of ghostscript](https://ghostscript.com/licensing/index.html) uses a [AGLPv3](https://www.gnu.org/licenses/agpl-3.0.en.html) license (strong copy-left license, i.e. all code in a project that uses ghostscript must be made available as open-source with the same license) but also offers a commercial license. Therefore the project is also bined to AGLPv3 license. 
If there is a way to replace ghostscript, I would be happy to publish the code under a more liberal scheme.

## Release & Version
- **0.1.1** bugfix initial release

## Status
maintenance + minor feature development

