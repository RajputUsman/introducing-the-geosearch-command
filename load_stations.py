import redis
import os

from fastkml import kml

STATIONS_KEY = "stations"

redis_client = redis.Redis(host = os.environ.get("REDIS_HOST",
    default="localhost"), decode_responses = True)

doc = open("stations.kml", "r").read()
stations_kml = kml.KML()
stations_kml.from_string(doc)

features = list(stations_kml.features())
stations = list(features[0].features())

pipeline = redis_client.pipeline(transaction=False)
pipeline.delete(STATIONS_KEY)

for station in stations:
    extended_data = station.extended_data
    sd = extended_data.elements[0]
    station_data = {x["name"]: x["value"] for x in sd.data}

    station_key = f"station:{str(station.name).lower()}"
    pipeline.hmset(station_key, station_data)
    pipeline.geoadd(STATIONS_KEY, station.geometry.x, station.geometry.y, station.name)

pipeline.zcard(STATIONS_KEY)
responses = pipeline.execute()

print(f"Loaded {responses[len(responses) -1]} stations.")
