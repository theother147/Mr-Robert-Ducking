#!/bin/sh

./bin/ollama serve &
sleep 5

ollama run codellama

exec "$@"