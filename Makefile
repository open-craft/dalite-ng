requirements: .requirements-timestamp

test-requirements: .test-requirements-timestamp

test: test-requirements
	coverage run --source=. manage.py test

coverage-report:
	coverage report -m

.%-timestamp: %.txt
	pip install -r "$<"
	touch "$@"

.PHONY: requirements test-requirements test coverage-report
