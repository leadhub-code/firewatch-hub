venv_dir=local/venv
python3=python3.5

check: $(venv_dir)/packages-installed
	$(venv_dir)/bin/pytest -v tests

$(venv_dir)/packages-installed: Makefile setup.py
	test -d $(venv_dir) || $(python3) -m venv $(venv_dir)
	$(venv_dir)/bin/pip install -U pip
	$(venv_dir)/bin/pip install pytest
	$(venv_dir)/bin/pip install -e .
	touch $@
