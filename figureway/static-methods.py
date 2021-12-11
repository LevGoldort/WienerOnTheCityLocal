import osmium
import json
import time
import pickle
from figureway.wiener import distance
import os
import sys


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
ISRAEL_OSM = "/Users/levgoldort/Downloads/israel-and-palestine-latest.osm.pbf"
SIBERIA_OSM = '/Users/levgoldort/Downloads/siberian-fed-district-latest.osm.pbf'
AMS_OSM = '/Users/levgoldort/Downloads/planet_4.7987,52.3077_5.0326,52.4135.osm.pbf'


def load_city_list(file_path):
    # Load list of all the cities to JSON
    with open(file_path, 'r') as file:
        city_json = json.load(file)
    return city_json


def drop_crossroads(osm_file_path, cities_json, destination_folder_path, country_filter=[], city_filter=[]):
    # Getting the crossroads from osm_file_path, matches them with cities_json and drops to destination_folder_path
    w = GenerateGraphHandler()
    w.apply_file(osm_file_path, locations=True)
    filtered_cities = [element for element in cities_json if
                       (not country_filter or element['country'] in country_filter) and
                       (not city_filter or element['name'] in city_filter)]
    current_directory = os.getcwd()
    final_directory = os.path.join(current_directory, destination_folder_path)
    if not os.path.exists(final_directory):
        os.makedirs(final_directory)
    for city in filtered_cities:
        crossroads = w.pick_crossroads(float(city['lat']), float(city['lng']), CITY_RAD)
        with open(destination_folder_path+city['name']+'.pickle', 'wb') as handle:
            pickle.dump(crossroads, handle)


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


def main():
    if len(sys.argv) == 1:
        city_list = load_city_list('./Static_data/cities.json')
        osm = AMS_OSM
        destination_source = 'Static_data/City_data/'
    else:
        osm, city_list, destination_source = arg[1:3]

    drop_crossroads(osm, city_list, destination_source, country_filter=['NL'], city_filter=['Amsterdam'])


if __name__ == '__main__':
    main()