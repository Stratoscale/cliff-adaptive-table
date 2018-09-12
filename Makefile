all: flake8 sdist

flake8:
	flake8 .

sdist:
	python setup.py sdist
