#!/bin/sh

./bin/ollama serve &
pid=$!
sleep 5

ollama run codellama
wait $pid