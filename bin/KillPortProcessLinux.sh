#!/bin/bash
#
# Script Name: WiFiSetup.sh
#
# Author: Mojtaba Mansour Abadi
# Date : 21 March 2018
#
# Description: Use this script to kill the process using a specific port
#
# Run Information: needs root permission to run
#
# Usage: sudo ./KillPortProcessLinux.sh
#

clear

FN=tempfile

port=$1

# echo $1 > text.txt

sudo fuser -n tcp $port > FN

test -s FN
if [ $? -eq 0 ]
then
echo The process "$(< FN)" is using port $port
sudo kill "$(< FN)"
else
echo No process is using port $port
fi

sudo rm FN

sleep 1s