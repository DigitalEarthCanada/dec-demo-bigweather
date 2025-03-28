#!/bin/bash

docker build -t harbor.dec.alpha.canada.ca/bigweather/precipitations:0.0.10 .
docker push harbor.dec.alpha.canada.ca/bigweather/precipitations:0.0.10
