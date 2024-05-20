setup: 
  pyenv local
  python -m venv .venv

build:
  python setup.py sdist bdist_wheel
