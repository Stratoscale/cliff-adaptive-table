all: flake8 sdist

flake8:
	flake8 .

sdist:
	python setup.py sdist

clean:
	rm -rf dist reports *.egg-info build logs .eggs .cache
	find -name "*.pyc" -delete
