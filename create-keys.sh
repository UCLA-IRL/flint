#!/usr/bin/env bash

app_prefix="ndn-compute"
entities=("driver" "worker")

mkdir -p sec_data/

# Do a dumb thing: run ndn fw to keep the container running forever until we get our keys
# (i swear, this image doesn't have cat or any other sane command to do this)
curl -s "https://raw.githubusercontent.com/named-data/ndnd/main/fw/yanfd.sample.yml" > sec_data/fw.yaml
container_id=$(docker run -v "$(pwd)/sec_data":/sec_data -d ghcr.io/named-data/ndnd fw run /sec_data/fw.yaml)

echo "create-keys: using docker container with id ${container_id}"

for entity in "${entities[@]}"; do
  mkdir -p sec_data/${entity}
  docker exec -i "${container_id}" /ndnd sec keygen /${app_prefix}/${entity} ecc secp256r1 > sec_data/${entity}/${entity}.key
  docker exec -i "${container_id}" /ndnd sec sign-cert /sec_data/${entity}/${entity}.key < sec_data/${entity}/${entity}.key > sec_data/${entity}/${entity}.cert
done

echo "create-keys: cleaning up"

rm sec_data/fw.yaml

docker stop "${container_id}" > /dev/null
docker rm "${container_id}" > /dev/null

echo "create-keys: done"
