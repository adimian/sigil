#!/bin/bash
export PYTHONPATH=sigil
py.test --cov sigil --cov-report html
open htmlcov/index.html
