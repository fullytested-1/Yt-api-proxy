#!/bin/bash

node /pot/server/build/main.js --port 4416 &
sleep 5

uvicorn main:app --host 0.0.0.0 --port 8000
