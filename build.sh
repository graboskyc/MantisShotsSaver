#!/bin/bash

echo
echo "+================================"
echo "| START: mantis"
echo "+================================"
echo

source backend/.env

datehash=`date | md5sum | cut -d" " -f1`
abbrvhash=${datehash: -8}
echo "Using conn string ${MDBCONNSTR}"
echo "Using username ${USERNAME}"

echo 
echo "Building container using tag ${abbrvhash}"
echo
docker build -t graboskyc/mantis:latest -t graboskyc/mantis:${abbrvhash} .

EXITCODE=$?

if [ $EXITCODE -eq 0 ]
    then

    echo 
    echo "Starting container"
    echo
    docker stop mantis
    docker rm mantis
    docker run -t -i -d -p 8000:8000 --name mantis -e "MDBCONNSTR=${MDBCONNSTR}" -e "USERNAME=${USERNAME}" --restart unless-stopped graboskyc/mantis:${abbrvhash}

    echo
    echo "+================================"
    echo "| END:  mantis"
    echo "+================================"
    echo
else
    echo
    echo "+================================"
    echo "| ERROR: Build failed"
    echo "+================================"
    echo
fi