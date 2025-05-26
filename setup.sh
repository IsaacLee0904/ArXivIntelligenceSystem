# Create docker network if it doesn't exist
docker network create arxiv_network 2>/dev/null || true

# Build the docker image
docker build -t arxiv_env:latest . 

# Run the docker container
docker run -d --restart always --name arxiv_env --network arxiv_network -v /etc/localtime:/etc/localtime:ro -v $(pwd):/app --privileged arxiv_env:latest tail -f /dev/null
