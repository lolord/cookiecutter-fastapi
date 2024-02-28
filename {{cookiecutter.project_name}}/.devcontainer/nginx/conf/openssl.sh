#! /bin/bash
openssl req -x509 -nodes -days 3650 -subj "/C=CN/CN=117.50.0.63" -newkey rsa:2048 -keyout server.key -out server.crt
