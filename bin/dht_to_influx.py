#!/usr/bin/env python3

from __future__ import absolute_import, print_function

"""
  How to use `aiohttp-retry` with async client.

  This example depends on `aiohttp_retry <https://github.com/inyutin/aiohttp_retry>`_.
  Install ``aiohttp_retry`` by: pip install aiohttp-retry.

"""
import os
import sys
import time
import random
import asyncio

import Adafruit_DHT

from aiohttp_retry import ExponentialRetry, RetryClient

from influxdb_client import Point
from influxdb_client.client.influxdb_client_async import InfluxDBClientAsync

import configparser

CONFIG_FILE = '/etc/dht_sensors.rc'

# ------------------------------------------------------------------------------------------------


def get_config_section(section):
    """
      read config file
    """
    config = configparser.RawConfigParser()
    config.read(CONFIG_FILE)

    return dict(config.items(section))


def truncate(n, decimals=0):
    """
    """
    multiplier = 10 ** decimals
    return int(n * multiplier) / multiplier


def sensor_read(sensor_model=22, sensor_pin=4, verbose=False, test=False):
    """
        read DHT sensor data
    """
    humidity = None
    temperature = None

    if test:
        humidity    = random.uniform(30, 100)
        temperature = random.uniform(10, 20)
    else:
        while True:
            try:
                humidity, temperature = Adafruit_DHT.read_retry(
                    sensor_model, sensor_pin
                )
            except ValueError as error:
                print(error)
                break

            if humidity is None or temperature is None:
                time.sleep(1)
                continue
            else:
                break

    if verbose:
        print(f"humidity   : {humidity}")
        print(f"temperature: {temperature}")

    return truncate(humidity, 1), truncate(temperature, 1)


async def write_to_influx(influx_config=dict(), sensor_config=dict(), location_config=dict()):
    """
        Configure Retries - for more info see https://github.com/inyutin/aiohttp_retry
    """
    retry_options = ExponentialRetry(attempts=3)

    sensor_model = int(sensor_config.get("model", 22))
    sensor_pin = int(sensor_config.get("pin", 4))
    sensor_measurement_name = sensor_config.get("measurement_name", "dht22")
    sensor_verbose = bool(sensor_config.get("verbose", False))
    sensor_test = bool(sensor_config.get("test", False))

    location_host = location_config.get("host", None)
    location_name = location_config.get("name", None)

    influx_url    = influx_config.get("url", None)
    influx_token  = influx_config.get("token", None)
    influx_org    = influx_config.get("org", None)
    influx_bucket = influx_config.get("bucket", None)
    influx_verbose = bool(influx_config.get("verbose", False))

    if not location_host or not location_name:
        print("Location data are not available!")
        print("Please define host and name.")
        sys.exit(1)

    if not influx_url or not influx_token or not influx_org or not influx_bucket:
        print("The configuration for InfluxDB is incomplete!")
        print("Please specify url, token, org and bucket.")
        sys.exit(1)

    humidity, temperature = sensor_read(
        sensor_model=sensor_model, sensor_pin=sensor_pin, verbose=sensor_verbose, test=sensor_test
    )

    async with InfluxDBClientAsync(
        url=influx_url, token=influx_token, org=influx_org, client_session_type=RetryClient,
        client_session_kwargs={"retry_options": retry_options}
    ) as client:
        """
          Write data:
        """
        if influx_verbose:
            print("\n------- Written data: -------\n")

        write_api = client.write_api()

        _point1 = Point(sensor_measurement_name) \
            .tag("host", location_host) \
            .tag("location", location_name) \
            .field("humidity", humidity)
        _point2 = Point(sensor_measurement_name) \
            .tag("host", location_host) \
            .tag("location", location_name) \
            .field("temperature", temperature)

        successfully = await write_api.write(
            bucket=influx_bucket, record=[_point1, _point2]
        )

        if influx_verbose:
            print(f" > successfully: {successfully}")

        # """
        #   Query: Stream of FluxRecords
        # """
        # print(f"\n------- Query: Stream of FluxRecords -------\n")
        # query_api = client.query_api()
        # records = await query_api.query_stream(f"from(bucket:{influx_bucket}) "
        #                                        "|> range(start: -10m) "
        #                                        "|> filter(fn: (r) => r['_measurement'] == 'dht22')"
        # )
        # async for record in records:
        #     print(record)

if __name__ == "__main__":
    """
      main function
    """
    if not os.path.exists(CONFIG_FILE):
        print(f"The configuration file '{CONFIG_FILE}' does not exist!")
        sys.exit(1)

    influx_config = get_config_section("influx")
    sensor_config = get_config_section("sensor")
    location_config = get_config_section("location")
    process_config = get_config_section("process")

    sleep = int(process_config.get("sleep", 60))

    while True:
        asyncio.run(
            write_to_influx(influx_config, sensor_config, location_config)
        )

        time.sleep(sleep)
