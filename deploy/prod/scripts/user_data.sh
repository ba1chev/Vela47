#!/bin/bash
# First boot of the Vela47 server instance, run once by cloud-init. Its output is in
# /var/log/cloud-init-output.log. It brings the Docker Engine to a version whose bridge
# networks support an isolated gateway (the sandbox relies on it), starts Ollama on the GPU
# and pulls the models, then builds the server from a clone of the repository and starts it.
# Both containers restart with Docker, so a reboot needs none of this again.
# It is a Terraform template, not a script to run as it is: main.tf fills in its placeholders
# through templatefile(), and a dollar sign that bash should see before a brace is doubled.
set -euxo pipefail
export DEBIAN_FRONTEND=noninteractive

# Docker Engine 28 or newer (gateway_mode_ipv4: isolated)
systemctl start docker || true
docker_major=$(docker version --format '{{.Server.Version}}' 2>/dev/null | cut -d. -f1 || true)
if [ "$${docker_major:-0}" -lt 28 ]; then
  for package in docker.io docker-doc docker-compose docker-compose-v2 podman-docker containerd runc; do
    apt-get remove -y "$package" || true
  done
  rm -f /etc/apt/sources.list.d/docker.list /etc/apt/sources.list.d/docker.sources
  install -m 0755 -d /etc/apt/keyrings
  curl -fsSL https://download.docker.com/linux/ubuntu/gpg -o /etc/apt/keyrings/docker.asc
  chmod a+r /etc/apt/keyrings/docker.asc
  echo "deb [arch=$(dpkg --print-architecture) signed-by=/etc/apt/keyrings/docker.asc] https://download.docker.com/linux/ubuntu $(. /etc/os-release && echo "$VERSION_CODENAME") stable" > /etc/apt/sources.list.d/docker.list
  apt-get update
  apt-get install -y docker-ce docker-ce-cli containerd.io
fi

# GPU access for containers (the NVIDIA Container Toolkit ships with the Deep Learning AMI)
nvidia-ctk runtime configure --runtime=docker
systemctl enable docker
systemctl restart docker
command -v git || { apt-get update && apt-get install -y git; }

# Network shared by the server and Ollama, neither publishes anything but the server port
docker network inspect ${app_network_name} >/dev/null 2>&1 || docker network create --driver bridge --subnet ${app_network_subnet} ${app_network_name}

# Ollama on the GPU, with the models the server uses
docker volume create ${ollama_volume_name}
docker rm -f ${ollama_container_name} 2>/dev/null || true
docker run --detach --name ${ollama_container_name} --restart unless-stopped --gpus all \
  --network ${app_network_name} --volume ${ollama_volume_name}:/root/.ollama \
  --env OLLAMA_MAX_LOADED_MODELS=${ollama_max_loaded} \
  --env OLLAMA_NUM_PARALLEL=${ollama_num_parallel} \
  ${ollama_image}
until docker exec ${ollama_container_name} ollama list >/dev/null 2>&1; do sleep 2; done
for model in ${ollama_models}; do
  docker exec ${ollama_container_name} ollama pull "$model"
done

# The server, built from the repository
rm -rf /opt/vela47
git clone --depth 1 --branch ${repository_branch} ${repository_url} /opt/vela47
docker build --tag ${app_image_name} --file /opt/vela47/deploy/prod/images/app_image/Dockerfile /opt/vela47
docker rm -f ${app_container_name} 2>/dev/null || true
docker run --detach --name ${app_container_name} --restart unless-stopped --init \
  --network ${app_network_name} --publish ${app_port}:8000 \
  --volume /var/run/docker.sock:/var/run/docker.sock \
  --env VELA47_ENVIRONMENT=prod \
  --env VELA47_AWS_REGION=${aws_region} \
  --env VELA47_DATABASE_HOST=${database_host} \
  --env VELA47_DATABASE_PORT=${database_port} \
  --env VELA47_DATABASE_NAME=${database_name} \
  --env VELA47_DATABASE_SECRET_ID=${database_secret_id} \
  --env VELA47_APP_SECRET_ID=${app_secret_id} \
  --env OLLAMA_HOST=http://${ollama_container_name}:11434 \
  ${app_image_name}
