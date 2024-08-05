.PHONY: package fmt lint dev_install test coverage clean push_pypi

package:
	python setup.py bdist_wheel

fmt:
	black pls

lint:
	pylama pls/

dev_install:
	pip install -e . --quiet

test: dev_install
	pytest --cov .

coverage: dev_install
	pytest --cov --cov-report html .

clean:
	rm -rf build dist pls.egg-info htmlcov

# Need to configure .pypirc with credentials
push_pypi:
	python -m twine upload --repository pls dist/*
