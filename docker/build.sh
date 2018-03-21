#!/bin/bash
REPO=docker-reg.emotibot.com.cn:55688
CONTAINER=robotwriter
DATE=`date +%Y%m%d`
TAG=$1
GIT_HASH=$(git rev-parse --short HEAD)
if [ "$GIT_HASH" == "" ]; then
    GIT_HASH="001"
fi
if [ ! "$TAG" ]; then
    TAG="$DATE-$GIT_HASH"
fi
DOCKER_IMAGE=$REPO/$CONTAINER:$TAG

DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
BUILDROOT=$DIR/..


# Build docker
cmd="docker build -t $DOCKER_IMAGE -f $DIR/Dockerfile $BUILDROOT"
echo $cmd
eval $cmd
