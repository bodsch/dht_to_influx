# dht_to_influx

Pushed DHT sensor data into an InfluxDB.

This works similar to my dht_exporter for a Prometheus.

## Configuration

```ini
[influx]
url    =
token  =
org    =
bucket =

[sensor]
pin   = 4
model = 22
measurement_name = dht22
test = false
verbose = false

[location]
host     = sensor-0x
name     =

[process]
sleep = 60
```

## install


```bash
git clone https://github.com/bodsch/dht_to_influx.git

bash dht_to_influx/install.sh

# edit /etc/dhtsensors.rc!

sudo systemctl enable --now dht-push-to-influx.service
```
