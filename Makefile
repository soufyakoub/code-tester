run :
	docker-compose up --build

test :
	python -m pytest -d -v -n auto --cov=src --rootdir=tests tests/specs
	coverage html

req :
	pipenv lock --dev -r > requirements.txt
