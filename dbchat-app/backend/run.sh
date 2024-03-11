#!/bin/bash
IMAGE_NAME=dbchat
APP_NAME=dbchat

# Move into source directory
cd dbchat

# # stop and remove image in case this script was run before
docker stop ${APP_NAME}
docker rm ${APP_NAME}

# # rebuild and run the new image
docker build -t ${IMAGE_NAME} .
docker run -d --name ${APP_NAME} -p 8000:8000 ${IMAGE_NAME}

# wait for the /health endpoint to return a 200 and then move on
finished=false
while ! $finished; do
    health_status=$(curl -o /dev/null -s -w "%{http_code}\n" -X GET "http://localhost:8000/health")
    if [ $health_status == "200" ]; then
        finished=true
        echo "API is ready"
    else
        echo "API not responding yet"
        sleep 1
    fi
done

# # check a few endpoints and their http response
# curl -o /dev/null -s -w "%{http_code}\n" -X GET "http://localhost:8000/hello?name=Winegar" # 200
# curl -o /dev/null -s -w "%{http_code}\n" -X GET "http://localhost:8000/hello?nam=Winegar" # 422
# curl -o /dev/null -s -w "%{http_code}\n" -X GET "http://localhost:8000/" # 404
# curl -o /dev/null -s -w "%{http_code}\n" -X GET "http://localhost:8000/docs" # 200

# curl -X 'POST' \
#   'http://127.0.0.1:8000/predict/' \
#   -H 'accept: application/json' \
#   -H 'Content-Type: application/json' \
#   -d '{
#   "MedInc": 8.924,
#   "HouseAge": 34,
#   "AveRooms": 4,
#   "AveBedrms": 2,
#   "Population": 3241,
#   "AveOccup": 22,
#   "Latitude": 123.45,
#   "Longitude": -145.67
# }' # 200

# # output logs for the container
# docker logs ${APP_NAME}

# # stop and remove container
# docker stop ${APP_NAME}
# docker rm ${APP_NAME}

# # delete image
# docker image rm ${APP_NAME}
