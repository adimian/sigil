#!/bin/bash
echo "Running build for sigil"
find . -name "*.pyc" -delete
docker build -t registry.adimian.com/sigil/sigil . && \
docker run --rm -t registry.adimian.com/sigil/sigil py.test && \
docker push registry.adimian.com/sigil/sigil
