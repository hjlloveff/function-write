#!/bin/bash
REPO=docker-reg.emotibot.com.cn:55688
CONTAINER=robotwriter-webapp
TAG=$(git rev-parse --short HEAD)
DOCKER_IMAGE=$REPO/$CONTAINER:$TAG

# Get env from env file
source $1
if [ $? -ne 0 ]; then
  echo "# Usage: run.sh <envfile>"
  exit 0
fi

docker rm -f -v $CONTAINER
cmd="docker run -d --name $CONTAINER \
 -e CONTENT_SERVER=$CONTENT_SERVER \
 -e CONTENT_KEY=$CONTENT_KEY \
 -e DOCKER_PORT=$DOCKER_PORT \
 -v /etc/localtime:/etc/localtime \
 -p $DOCKER_PORT:$DOCKER_PORT \
   $DOCKER_IMAGE \
"

echo $cmd
eval $cmd
