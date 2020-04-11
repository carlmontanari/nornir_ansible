lint:
	python -m isort -rc -y .
	python -m black .
	python -m pylama .
	python -m pydocstyle .
	python -m mypy nornir_ansible/

test:
	python -m pytest tests/

cov:
	python -m pytest \
	--cov=nornir_ansible \
	--cov-report html \
	--cov-report term \
	tests/