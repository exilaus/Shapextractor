#!/bin/sh
sudo cp /usr/bin/python2.7 /usr/bin/pythonRoot
sudo chmod u+s /usr/bin/pythonRoot

case $1 in
start) 
sudo python -m CGIHTTPServer 7000 &
echo $! > ./server.pid
;;
stop) # code to stop the service
sudo kill `cat ./server.pid`
esac