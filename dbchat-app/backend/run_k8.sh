# Move into source directory
cd dbchat

# Start up Minikube
echo "Starting minikube..."
minikube start --kubernetes-version=v1.27.3

# Setup your docker daemon to build with Minikube
echo "Setup docker daemon..."
eval $(minikube docker-env)

# Build the docker container of your application
echo "Build docker image..."
docker build -t dbchat:latest .

# Apply your k8s namespace
echo "Apply K8 namespace..."
kubectl apply -f infra/namespace.yaml
kubectl config set-context --current --namespace=w255

# Apply your Deployments and Services
echo "Apply K8 deployments and services..."
kubectl apply -f infra/deployment-redis.yaml --namespace=w255 # redis
kubectl apply -f infra/service-redis.yaml --namespace=w255
kubectl apply -f infra/deployment-pythonapi.yaml --namespace=w255 # prediction api
kubectl apply -f infra/service-prediction.yaml --namespace=w255

# Wait for all pods to be up and running
echo "Waiting for pods to be ready..."
while true; do
  # Use kubectl to get pod status for each pod
  predict_status=$(kubectl get pods --namespace=w255 | grep 'deployment-predict' | awk '{print $2}')
  redis_status=$(kubectl get pods --namespace=w255 | grep 'deployment-redis' | awk '{print $2}')
  
  # Check if both pods are in a running state
  expected_status="1/1"
  if [ "$predict_status" == "$expected_status" ] && [ "$redis_status" == "$expected_status" ]; then
    echo "All pods are up and running."
    break
  else
    echo "Waiting for pods to be ready..."
    sleep 5
  fi
done

# Capture the output of the kubectl command
pods_output=$(kubectl get pods --namespace=w255)

# Show the captured output
echo "$pods_output"

# Port-forward a local port on your machine to your API service
echo "Port forwarding API service..."
kubectl port-forward service/predict-service 8000:8000 &

# Wait for the API to be accessible
while true; do
  STATUS_CODE=$(curl -s -o /dev/null -w "%{http_code}" http://localhost:8000/health)
  if [ $STATUS_CODE -eq 200 ]; then
    echo "API is accessible."
    break
  else
    echo "Waiting for the API to be accessible... (HTTP $STATUS_CODE)"
    sleep 5
  fi
done

# Validate all Lab 1 Endpoints
curl -o /dev/null -s -w "%{http_code}\n" -X GET "http://localhost:8000/hello?name=Winegar" # 200
curl -o /dev/null -s -w "%{http_code}\n" -X GET "http://localhost:8000/hello?nam=Winegar" # 422
curl -o /dev/null -s -w "%{http_code}\n" -X GET "http://localhost:8000/" #404
curl -o /dev/null -s -w "%{http_code}\n" -X GET "http://localhost:8000/docs" # 200

# Validate all Lab 2/3 Endpoints
curl -o /dev/null -s -w "%{http_code}\n" -X POST "http://localhost:8000/predict" -H 'Content-Type: application/json' -d '{
    "MedInc": 1,
    "HouseAge": 1,
    "AveRooms": 3,
    "AveBedrms": 3,
    "Population": 3,
    "AveOccup": 5,
    "Latitude": 1,
    "Longitude": 1
}' # 200

curl -X 'POST' \
  'http://127.0.0.1:8000/bulk_prediction' \
  -H 'accept: application/json' \
  -H 'Content-Type: application/json' \
  -d '{
  "houses": [
    {
      "MedInc": 1,
      "HouseAge": 1,
      "AveRooms": 1,
      "AveBedrms": 1,
      "Population": 1,
      "AveOccup": 1,
      "Latitude": 0,
      "Longitude": 0
    },
    {
      "MedInc": 1,
      "HouseAge": 2,
      "AveRooms": 3,
      "AveBedrms": 4,
      "Population": 5,
      "AveOccup": 1.23,
      "Latitude": 123,
      "Longitude": 345
    }
  ]
}' # 200

curl -X 'POST' \
  'http://127.0.0.1:8000/bulk_prediction' \
  -H 'accept: application/json' \
  -H 'Content-Type: application/json' \
  -d '{
  "houses": [
    {
      "MedInc": 1,
      "HouseAge": 1,
      "AveRooms": -1,
      "AveBedrms": 1,
      "Population": 1,
      "AveOccup": 1,
      "Latitude": 0,
      "Longitude": 0
    },
    {
      "MedInc": 1,
      "HouseAge": 2,
      "AveRooms": 3,
      "AveBedrms": 4,
      "Population": 5,
      "AveOccup": 1.23,
      "Latitude": 123,
      "Longitude": 345
    }
  ]
}'

# Delete all resources
kubectl delete all --all

# Stop Minikube
minikube stop
minikube delete
