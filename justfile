latest:
  python scripts/mbdl.py --latest
  
generate_all:
  python scripts/mbdl.py

setup: 
  pyenv local
  python -m venv .venv

build:
  python setup.py sdist bdist_wheel
