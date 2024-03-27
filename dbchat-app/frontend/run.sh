#!/bin/bash
cd dbchat-frontend

RESOURCE_NM="dbchat_streamlit"
NETWORK_NM="dbchat_network"
CONTAINER_ID=$(docker ps -aqf "name=${RESOURCE_NM}")
IMAGE_ID=$(docker images -qf "reference=${RESOURCE_NM}")
DOCKERFILE_NAME="Dockerfile.streamlit"

docker rm -f "$CONTAINER_ID"
docker rmi -f "$IMAGE_ID"
docker build -t ${RESOURCE_NM} -f ${DOCKERFILE_NAME} .
docker run -d -p 8501:8501 --name ${RESOURCE_NM} --network ${NETWORK_NM} ${RESOURCE_NM}
