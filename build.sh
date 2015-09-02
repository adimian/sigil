#!/bin/bash
echo "Running build for sigil"
docker build -t registry.adimian.com/sigil/sigil .
docker push registry.adimian.com/sigil/sigil
