#!/bin/bash

# Set variables
container_id=$(docker ps -aqf "name=mysql-container")
container_name="mysql-container"
image_name="mysql/mysql-server:latest"
network_name="dbchat_network"

echo ${container_id}
echo ${container_name}
echo ${image_name}
echo ${network_name}

# Remove existing containers and images
docker rm -f ${container_id}
docker rmi -f $(docker images ${image_name} -a -q)

# Pull docker image
docker pull ${image_name}

# Run docker container
docker run --name ${container_name} --network ${network_name} -e MYSQL_ROOT_PASSWORD=your_password -d ${image_name}

# New docker container
container_id=$(docker ps -aqf "name=mysql-container")
echo ${container_id}

# Wait for MySQL to start
echo "Waiting for MySQL to start..."
sleep 30

# Copy files into docker container
docker cp ./dbchat/dbchat/assets/1-init.sql ${container_id}:/
docker cp ./dbchat/dbchat/assets/2-sakila-schema.sql ${container_id}:/
docker cp ./dbchat/dbchat/assets/3-sakila-data.sql ${container_id}:/

# Run SQL script in docker container
docker exec ${container_id} /bin/sh -c 'mysql -u root -pyour_password <1-init.sql'
docker exec ${container_id} /bin/sh -c 'mysql -u root -pyour_password <2-sakila-schema.sql'
docker exec ${container_id} /bin/sh -c 'mysql -u root -pyour_password <3-sakila-data.sql'

# Exec into docker container
docker exec -it ${container_name} mysql -u newuser -pnewpassword