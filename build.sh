#!/bin/bash

echo
echo "+================================"
echo "| START: pfam"
echo "+================================"
echo

source backend/.env

datehash=`date | md5sum | cut -d" " -f1`
abbrvhash=${datehash: -8}
echo "Using conn string ${MDBCONNSTR}"

echo 
echo "Building container using tag ${abbrvhash}"
echo
docker build -t graboskyc/pfam:latest -t graboskyc/pfam:${abbrvhash} .

EXITCODE=$?

if [ $EXITCODE -eq 0 ]
    then

    echo 
    echo "Starting container"
    echo
    docker stop pfam
    docker rm pfam
    docker run -t -i -d -p 8000:8000 --name pfam -e "MDBCONNSTR=${MDBCONNSTR}" --restart unless-stopped graboskyc/pfam:${abbrvhash}

    echo
    echo "+================================"
    echo "| END:  pfam"
    echo "+================================"
    echo
else
    echo
    echo "+================================"
    echo "| ERROR: Build failed"
    echo "+================================"
    echo
fi