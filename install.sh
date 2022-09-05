#!/usr/bin/env bash

dir=$(dirname $(find . -type f -name dht_to_influx.py))

sudo cp -av "${dir}/../init/systemd/dht-push-to-influx.service" /lib/systemd/system/

sudo cp -av "${dir}/../bin/dht_to_influx.py" /bin/
sudo cp -av "${dir}/../etc/dht_sensors.rc" /etc/

sudo chmod +x /bin/dht_to_influx.py

pip3 install -r ${dir}/../requirements.txt
