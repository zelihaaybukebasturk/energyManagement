#!/bin/bash

echo "Starting AI-Driven Building Energy Efficiency System..."
echo ""

echo "Starting backend server..."
python start_server.py &
BACKEND_PID=$!

sleep 3

echo "Starting frontend server..."
python serve_frontend.py &
FRONTEND_PID=$!

echo ""
echo "Both servers are starting..."
echo "Backend API: http://localhost:8000"
echo "Frontend: http://localhost:8080"
echo ""
echo "Press Ctrl+C to stop both servers"

# Wait for user interrupt
trap "kill $BACKEND_PID $FRONTEND_PID; exit" INT
wait
