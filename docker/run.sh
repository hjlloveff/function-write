#!/bin/bash
REPO=docker-reg.emotibot.com.cn:55688
CONTAINER=webapp-template
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
 -e DOCKER_PORT=$DOCKER_PORT \
 -e MYSQL_DB_SERVER=$MY_SQL_DB_SERVER \
 -e MYSQL_DB_USER=$MYSQL_DB_USER \
 -e MYSQL_DB_PASSWORD=$MYSQL_DB_PASSWORD \
 -e REDIS_SERVER=$REDIS_SERVER \
 -e REDIS_DB=$REDIS_DB \
 -v /etc/localtime:/etc/localtime \
 -p $DOCKER_PORT:$DOCKER_PORT \
   $DOCKER_IMAGE \
"

echo $cmd
eval $cmd
