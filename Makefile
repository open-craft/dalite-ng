requirements: .requirements-timestamp

test-requirements: .test-requirements-timestamp

test: test-requirements
	coverage run --source=. manage.py test

coverage-report:
	coverage report -m

.%-timestamp: requirements/%.txt
	pip install -r "$<"
	touch requirements/"$@"

.PHONY: requirements test-requirements test coverage-report
