venv_dir=local/venv
python3=python3.5

check: $(venv_dir)/packages-installed
	$(venv_dir)/bin/pytest -v tests

run: $(venv_dir)/packages-installed
	env \
		FLASK_DEBUG=1 \
		FLASK_APP=app \
		OAUTHLIB_INSECURE_TRANSPORT=1 \
		$(venv_dir)/bin/flask run

$(venv_dir)/packages-installed: Makefile setup.py
	test -d $(venv_dir) || $(python3) -m venv $(venv_dir)
	$(venv_dir)/bin/pip install -U pip
	$(venv_dir)/bin/pip install -U wheel
	$(venv_dir)/bin/pip install pytest
	$(venv_dir)/bin/pip install -e .
	touch $@

run-mongod:
	mkdir -p local/db-data
	mongod \
		--dbpath local/db-data \
		--port 27017 \
		--wiredTigerCacheSizeGB 1
