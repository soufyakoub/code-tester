# code-tester

> Write and run tests against sample code without setting up language environments.

# Usage

Make sure you have [docker][docker] and [docker-compose][docker-compose] installed, Then type `make run` in a terminal.

After the build has finished, you can access the UI in `http://localhost:80`.

# Getting started

These instructions will get you a copy of the project up and running on your local machine for development and testing purposes.

### Prerequisites

- [docker][docker] and [docker-compose][docker-compose] : Can be installed with `sudo apt install docker docker-compose`.

### Installation

Installing project dependencies is done using:

- [pip][pip] : `pip install -r requirements.txt`

    or

- [pipenv][pipenv] : `pipenv install --dev`

### Running tests

Running tests is as simple as typing `make test` in a terminal.

Coverage reports are located in `tests/coverage`. By default, terminal and html reports are generated.

If you need them as json or xml, just run `coverage json` or `coverage xml`.

[docker]: https://www.docker.com/
[docker-compose]: https://docs.docker.com/compose/
[pip]: https://pypi.org/project/pip/
[pipenv]: https://pypi.org/project/pipenv/
