#/bin/bash

echo "Stopping all running containers..."
docker stop $(docker ps -aq) 2>/dev/null

echo "Removing all containers..."
docker rm $(docker ps -aq) 2>/dev/null

echo "Removing all images..."
docker rmi $(docker images -q) 2>/dev/null

echo "Docker cleanup complete."