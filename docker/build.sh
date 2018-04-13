#!/bin/bash
REPO=docker-reg.emotibot.com.cn:55688
CONTAINER=robotwriter
DATE=`date +%Y%m%d`
TAG=
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

DOCKERFILE=$DIR/Dockerfile
PLATFORM=$1
if [[ $PLATFORM == "suse" ]] || [[ $PLATFORM == "SUSE" ]]; then
  DOCKERFILE=$DOCKERFILE"-SUSE"
  DOCKER_IMAGE=$DOCKER_IMAGE"-SUSE"
fi

# Build docker
cmd="docker build -t $DOCKER_IMAGE -f $DOCKERFILE $BUILDROOT"
echo $cmd
eval $cmd
