test:
	flake8 .
	python -m pytest --cov-report term-missing --cov restea
