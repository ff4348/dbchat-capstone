RESOURCE_NM="dbchat_frontend"
NETWORK_NM="dbchat_network"
CONTAINER_ID=$(docker ps -aqf "name=${RESOURCE_NM}")
IMAGE_ID=$(docker images -qf "reference=${RESOURCE_NM}")

docker rm -f "$CONTAINER_ID"
docker rmi -f "$IMAGE_ID"
docker build -t ${RESOURCE_NM} -f Dockerfile.chatbot .
docker run -d -p 3000:3000 --name ${RESOURCE_NM} --network ${NETWORK_NM} ${RESOURCE_NM}
