# code-tester [![Build Status](https://travis-ci.org/soufyakoub/code-tester.svg?branch=master)](https://travis-ci.org/soufyakoub/code-tester) [![codecov](https://codecov.io/gh/soufyakoub/code-tester/branch/master/graph/badge.svg)](https://codecov.io/gh/soufyakoub/code-tester)

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

Coverage reports are located in `tests/coverage`. By default, terminal and HTML reports are generated.

If you need them as **JSON** or **XML**, just run `coverage json` or `coverage xml`.

# Contributing

Please feel free to submit issues and pull requests.

# License

This project is licensed under the MIT License - see the [LICENSE](https://github.com/soufyakoub/code-tester/blob/master/LICENSE) file for details.

[docker]: https://www.docker.com/
[docker-compose]: https://docs.docker.com/compose/
[pip]: https://pypi.org/project/pip/
[pipenv]: https://pypi.org/project/pipenv/