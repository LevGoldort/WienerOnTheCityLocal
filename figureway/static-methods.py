import boto3
import osmium
import json
import time
import pickle
from figureway.wiener import distance
import os
import sys
import requests
import configparser
import csv


NAME_EN_TAG = "name:en"
STREET_HIGHWAY_TAGS = frozenset([  # OpenStreetMap tags related to roads.
    "service",
    "path",
    "residential",
    "footway",
    "tertiary",
    "secondary",
    "unclassified"
])
CITY_RAD = 10000  # Minimum distance to the closest city

#
# # degrees to radians
# # https://stackoverflow.com/questions/238260/how-to-calculate-the-bounding-box-for-a-given-lat-lng-location
# def deg2rad(degrees):
#     return math.pi * degrees / 180.0
#
#
# # radians to degrees
# def rad2deg(radians):
#     return 180.0 * radians/math.pi
#
#
# # Semi-axes of WGS-84 geoidal reference
# WGS84_a = 6378137.0  # Major semiaxis [m]
# WGS84_b = 6356752.3  # Minor semiaxis [m]
#
#
# # Earth radius at a given latitude, according to the WGS-84 ellipsoid [m]
# def WGS84EarthRadius(lat):
#     # http://en.wikipedia.org/wiki/Earth_radius
#     An = WGS84_a * WGS84_a * math.cos(lat)
#     Bn = WGS84_b * WGS84_b * math.sin(lat)
#     Ad = WGS84_a * math.cos(lat)
#     Bd = WGS84_b * math.sin(lat)
#     return math.sqrt((An * An + Bn * Bn)/(Ad * Ad + Bd * Bd))
#
#
# # Bounding box surrounding the point at given coordinates,
# # assuming local approximation of Earth surface as a sphere
# # of radius given by WGS84
# def boundingBox(latitudeInDegrees, longitudeInDegrees, halfSideInKm):
#     lat = deg2rad(latitudeInDegrees)
#     lon = deg2rad(longitudeInDegrees)
#     halfSide = 1000*halfSideInKm
#
#     # Radius of Earth at given latitude
#     radius = WGS84EarthRadius(lat)
#     # Radius of the parallel at given latitude
#     pradius = radius*math.cos(lat)
#
#     latMin = lat - halfSide/radius
#     latMax = lat + halfSide/radius
#     lonMin = lon - halfSide/pradius
#     lonMax = lon + halfSide/pradius
#
#     return (rad2deg(latMin), rad2deg(lonMin), rad2deg(latMax), rad2deg(lonMax))]
#
#
# def load_ways(min_lat, min_lon, max_lat, max_lon):
#     api = overpy.Overpass(url='https://overpass.kumi.systems/api/interpreter')
#
#     # fetch all ways and nodes
#     result = api.query("""
#         way({},{},{},{}) ["highway"];
#         (._;>;);
#         out body;
#         """.format(min_lat, min_lon, max_lat, max_lon))
#
#     for way in result.ways:
#         print("Name: %s" % way.tags.get("name", "n/a"))
#         print("  Highway: %s" % way.tags.get("highway", "n/a"))
#         print("  Nodes:")
#         for node in way.nodes:
#             print(node.id)
#             print("    Lat: %f, Lon: %f" % (node.lat, node.lon))


def load_city_list(file_path):
    # Load list of all the cities to JSON
    with open(file_path, 'r') as file:
        city_json = json.load(file)
    return city_json


def download_osm(url, dest):
    r = requests.get(url, allow_redirects=True)
    with open(dest, 'wb') as file:
        file.write(r.content)


def drop_crossroads(osm_file_path, cities_json, destination_folder_path, destination_type='local',
                    destination_bucket=None, s3_api_key=None, s3_secret_key=None, country_filter=[], city_filter=[]):
    # Getting the crossroads from osm_file_path, matches them with cities_json and drops to destination_folder_path
    w = GenerateGraphHandler()
    start = time.time()
    w.apply_file(osm_file_path, locations=True)
    print('file for {} applied in {}'.format(osm_file_path, time.time() - start))

    filtered_cities = [element for element in cities_json if
                       (not country_filter or element['country'] in country_filter) and
                       (not city_filter or element['name'] in city_filter)]
    print('CITIES FILTERED')

    if destination_type == 'local':
        if not os.path.exists(destination_folder_path):
            os.makedirs(destination_folder_path)
        for city in filtered_cities:
            destination_path = destination_folder_path + city['lat'] + city['lng'] + '.pickle'
            crossroads = w.pick_crossroads(float(city['lat']), float(city['lng']), CITY_RAD)
            with open(destination_path, 'wb') as handle:
                pickle.dump(crossroads, handle)
    else:
        session = boto3.Session(aws_access_key_id=s3_api_key, aws_secret_access_key=s3_secret_key)
        s3 = session.resource('s3')
        for city in filtered_cities:
            destination_path = destination_folder_path + city['lat'] + city['lng'] + '.pickle'
            crossroads = w.pick_crossroads(float(city['lat']), float(city['lng']), CITY_RAD)
            crossroads_bytes = pickle.dumps(crossroads)
            bucket = s3.create_bucket(Bucket=destination_bucket)
            result = s3.Object(destination_bucket, destination_path).put(Body=crossroads_bytes)

def load_crossroads(file_path):
    with open(file_path, 'rb') as handle:
        return pickle.load(handle)


def find_closest_city(lat, lon, city_list):
    closest_city = city_list[0]
    closest_distance = distance(lat, lon, float(city_list[0]['lat']), float(city_list[0]['lng']))
    for element in city_list:
        dist = distance(lat, lon, float(element['lat']), float(element['lng']))
        if dist < closest_distance:
            closest_city = element
            closest_distance = dist

    if closest_distance > CITY_RAD:
        return None
    else:
        return closest_city



def get_street_tag(tags):
    # Check OSM way tags to decide if it is a street
    if "highway" not in tags:
        return None

    if NAME_EN_TAG in tags:
        return NAME_EN_TAG

    if tags.get("highway") in STREET_HIGHWAY_TAGS:
        return "highway"
    return None


class GenerateGraphHandler(osmium.SimpleHandler):

    # Generates a graph of crossroads in radius in meters around the point (lat, lon)

    def __init__(self):
        super().__init__()
        self.all_way_dots = {}
        self.way_counter = {}

    def way(self, w):
        street_tag = get_street_tag(w.tags)
        if not street_tag:
            return
        print(dir(w.nodes))
        print(w.nodes.__repr__)
        for node in w.nodes:
            if node.ref not in self.all_way_dots.keys():
                # If node is not saved yet, then add it to dict of all dots
                self.all_way_dots[node.ref] = {
                    "lat": node.lat,
                    "lon": node.lon,
                    "x": node.x,
                    "y": node.y,
                    "neighbors": set()
                }
                self.way_counter[node.ref] = 0  # Number of different ways this node participate in
            for connected_node in w.nodes:
                # Add all nodes in the way as neighbors for this dot
                self.all_way_dots[node.ref]["neighbors"].add(connected_node.ref)
            self.all_way_dots[node.ref]["neighbors"].remove(node.ref)
            self.way_counter[node.ref] += 1

    def pick_crossroads(self, lat, lon, radius):
        crossroads_refs = {key for (key, value) in self.way_counter.items() if value > 1}  # pick all crossroad ids
        crossroads = {key: self.all_way_dots[key] for key in crossroads_refs if  # Match crossroads ids to node data
                      distance(self.all_way_dots[key]['lat'], self.all_way_dots[key]['lon'], lat, lon) < radius}
        for node_ref in crossroads:  # Saving in neighbors only nodes that are crossroads
            crossroads[node_ref]['neighbors'] = crossroads[node_ref]['neighbors'] & crossroads_refs
        return crossroads


def download_and_drop_country(cfg, countrycode):

    cfg.read(os.path.join(os.path.dirname(__file__), 'config.cfg'))
    city_list_path = cfg.get('INPUT_PATH', 'city_list', fallback='Wrong Config file')
    country_download_links = cfg.get('INPUT_PATH', 'country_list', fallback='Wrong Config file')

    destination_type = cfg.get('OUTPUT_PATH', 'destination_type', fallback='Wrong Config file')
    destination_path = cfg.get('OUTPUT_PATH', 'destination_path', fallback='Wrong Config file') + countrycode + '/'
    #destination_path = os.path.join(os.path.dirname(__file__), destination_folder_path)

    amazon_access_key_id = cfg.get('DEFAULT', 'aws_access_key_id')
    amazon_secret_key = cfg.get('DEFAULT', 'aws_secret_access_key')
    amazon_bucket_name = cfg.get('DEFAULT', 'aws_s3_bucket')

    country_links_list = list(csv.reader(open(os.path.join(os.path.dirname(__file__), country_download_links))))
    country = [element for element in country_links_list if element[0] == countrycode][0]

    dest = os.path.join(os.path.dirname(__file__), 'osm-file-dl' + '.osm.pbf')
    download_osm(country[2], dest)

    city_list = load_city_list(os.path.join(os.path.dirname(__file__), city_list_path))

    drop_crossroads(dest, city_list,
                    destination_folder_path=destination_path,
                    country_filter=[countrycode],
                    city_filter='',
                    destination_type=destination_type,
                    s3_api_key=amazon_access_key_id,
                    s3_secret_key=amazon_secret_key,
                    destination_bucket=amazon_bucket_name)

    os.remove(dest)


def main():
    start = time.time()
    cfg = configparser.ConfigParser()
    download_and_drop_country(cfg, 'MD')
    print('all executed in:', time.time() - start)




if __name__ == '__main__':
    main()