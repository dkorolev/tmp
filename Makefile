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
