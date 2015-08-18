#!/bin/bash
py.test --cov sigil --cov-report html
open htmlcov/index.html
