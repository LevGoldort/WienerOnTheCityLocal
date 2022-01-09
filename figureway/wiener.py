import osmium
import math
import logging
import staticmaps
import configparser
import os
import staticmethods as static
import pickle
import boto3
from distance import distance

NAME_EN_TAG = "name:en"
STREET_HIGHWAY_TAGS = frozenset([
    "service",
    "path",
    "residential",
    "footway",
    "secondary",
    "unclassified",

])

DIRECTION_RIGHT = 1
DIRECTION_LEFT = -1

penis_dict = [{"direction": -1, "length": 1},
              {"direction": 1, "length": 1},
              {"direction": 1, "length": 1},
              {"direction": -1, "length": 2},
              {"direction": 1, "length": 1},
              {"direction": 1, "length": 2},
              {"direction": -1, "length": 1},
              {"direction": 1, "length": 1},
              {"direction": 1, "length": 1}
              ]

#logging.basicConfig(filename='../figure_way_finder.log', level=logging.DEBUG)
class PointShower:

    def __init__(self):
        self.context = staticmaps.Context()
        self.context.set_tile_provider(staticmaps.tile_provider_OSM)

    def show_point(self, lat, lon, color=staticmaps.RED):

        map_center = staticmaps.create_latlng(lat, lon)
        self.context.add_object(staticmaps.Marker(map_center, color=color, size=10))

    def show_points_on_map(self, graph, point, points_list, second_points_list=[]):
        context = staticmaps.Context()
        context.set_tile_provider(staticmaps.tile_provider_OSM)

        map_center = staticmaps.create_latlng(graph[point]['lat'], graph[point]['lon'])
        context.add_object(staticmaps.Marker(map_center, color=staticmaps.RED, size=10))

        for element in points_list:
            element_center = staticmaps.create_latlng(graph[element]['lat'], graph[element]['lon'])
            context.add_object(staticmaps.Marker(element_center, color=staticmaps.BLUE, size=10))

        image = context.render_svg(1024, 800)

    def drop_image(self):
        image = self.context.render_svg(1024, 1024)
        image.save()


def rotate(ox, oy, px, py, angle):
    """
    Rotate a point counterclockwise by a given angle around a given origin.

    The angle should be given in radians.

    For clockwise - angle should be negated
    https://stackoverflow.com/questions/34372480/rotate-point-about-another-point-in-degrees-python/34374437
    """

    qx = ox + math.cos(angle) * (px - ox) - math.sin(angle) * (py - oy) / math.fabs(math.cos(math.radians(oy)))
    qy = oy + math.sin(angle) * (px - ox) * math.fabs(math.cos(math.radians(oy))) + math.cos(angle) * (py - oy)

    return qx, qy


def rotate_test(oy, ox, py, px, angle):
    """
    Rotate a point counterclockwise by a given angle around a given origin.

    The angle should be given in radians.

    For clockwise - angle should be negated
    https://stackoverflow.com/questions/34372480/rotate-point-about-another-point-in-degrees-python/34374437
    double x =  origion.longitude   + (Math.cos(Math.toRadians(degree)) * (point.longitude - origion.longitude) -
    Math.sin(Math.toRadians(degree))  * (point.latitude - origion.latitude) / Math.abs(Math.cos(Math.toRadians(origion.latitude)));
    double y = origion.latitude + (Math.sin(Math.toRadians(degree)) * (point.longitude - origion.longitude) *
    Math.abs(Math.cos(Math.toRadians(origion.latitude))) + Math.cos(Math.toRadians(degree))   * (point.latitude - origion.latitude));
    """
    shower = PointShower()
    shower.show_point(oy, ox)
    shower.show_point(py, px, staticmaps.GREEN)
    qx = ox + math.cos(angle) * (px - ox) - math.sin(angle) * (py - oy) / math.fabs(math.cos(math.radians(oy)))
    qy = oy + math.sin(angle) * (px - ox) * math.fabs(math.cos(math.radians(oy))) + math.cos(angle) * (py - oy)
    shower.show_point(qy, qx, staticmaps.BLUE)
    shower.drop_image()
    return qx, qy


def sign(x):
    if x >= 0:
        return 1
    return -1


def if_point_in_angle(ax, ay, bx, by, cx, cy, x, y):
    # a function to check if x,y in angle formed by 3 points A, B, C.
    # https://math.stackexchange.com/questions/1470784/find-if-a-point-lies-within-the-angle-formed-by-three-other-points

    j = ((y - ay) * (bx - ax) - (by - ay) * (x - ax)) \
        / ((cy - ay) * (bx - ax) - (by - ay) * (cx - ax))

    i = ((x - ax) - (cx - ax) * j) / (bx - ax)

    if i > 0 and j > 0:
        return True

    return False


def print_point_links(graph):
    # Test function to print links to points of graph
    for i in graph:
        print(i)
        print("https://www.google.com/maps/search/?api=1&query=" + str(graph[i]["lat"]) + "%2C" + str(
            graph[i]["lon"]))
        print(graph[i]["ways"])


def show_way_by_points(points, graph):
    # Test function to make a way visual. Returns link to Google Maps route
    address = "https://www.google.com/maps/dir/"
    for point in points:
        point_str = str(graph[point]["lat"]) + "," + str(graph[point]["lon"]) + "/"
        address = address + point_str
    return address


def show_way_by_lonlat(points):
    address = "https://www.google.com/maps/dir/"
    for point in points:
        point_str = str(point[0]) + "," + str(point[1]) + "/"
        address = address + point_str
    return address


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

    def __init__(self, lat, lon, rad):
        super().__init__()
        self.all_way_dots = {}
        self.way_counter = {}
        self.point_lat = lat
        self.point_lon = lon
        self.radius = rad

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

    def way_obsolete(self, w):
        #Old way function, saved for a while
        street_tag = get_street_tag(w.tags)
        if not street_tag:
            return
        for node in w.nodes:
            if distance(self.point_lat, self.point_lon, node.lat, node.lon) < self.radius:
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

    def pick_crossroads(self):
        crossroads_refs = {key for (key, value) in self.way_counter.items() if value > 1}  # pick all crossroad ids
        crossroads = {key: self.all_way_dots[key] for key in crossroads_refs}
        for node_ref in crossroads:
            crossroads[node_ref]['neighbors'] = crossroads[node_ref]['neighbors'] & crossroads_refs
        return crossroads


class FigureWayFinder:

    def __init__(self, figure, perimeter, distance_allowance, angle_allowance, graph):
        self.figure = figure
        self.edge = perimeter / len(figure)
        self.distance_allowance = distance_allowance
        self.angle_allowance = angle_allowance
        self.graph = graph
        self.ways_found = []
        logging.debug("FigureWayFinder initialized with figure {}, perimeter {}".format(figure, perimeter))

    def get_start_node(self, lat, lon):
        # Find the closest to (lat, lon) node in graph
        min_distance = 0
        min_point_id = None

        for node_ref in self.graph:
            node_distance = distance(lat, lon, self.graph[node_ref]["lat"], self.graph[node_ref]["lon"])
            if node_distance < min_distance or min_point_id is None:
                min_distance = node_distance
                min_point_id = node_ref
        return min_point_id

    def get_start_nodes(self, lat, lon, number_of_nodes):
        distances_dict = dict()
        for node_ref in self.graph:
            distances_dict[node_ref] = distance(lat, lon, self.graph[node_ref]["lat"], self.graph[node_ref]["lon"])
        sorted_dist = sorted(distances_dict, key=distances_dict.__getitem__)
        return sorted_dist[0:number_of_nodes]

    def is_in_correct_distance(self, distance_to_current_node, length):
        return (length * self.edge * self.distance_allowance
                < distance_to_current_node
                < length * self.edge * (2 - self.distance_allowance))

    def continue_straight(self, current_node_ref, prev_node_ref, usages_number=0):

        if usages_number > 3:
            return None
        usages_number += 1

        current_node = self.graph[current_node_ref]
        prev_node = self.graph[prev_node_ref]
        possible_ways = {}
        node_in_same_direction = {}

        for neighbor_ref in current_node['neighbors']:

            is_on_the_same_direction = self.node_direction_check(current_node, prev_node,
                                                                 self.graph[neighbor_ref], 2)
            distance_to_current_node = distance(current_node["lat"], current_node["lon"],
                                                self.graph[neighbor_ref]["lat"], self.graph[neighbor_ref]["lon"])
            if is_on_the_same_direction:  # and distance_to_current_node > self.edge / 4:
                node_in_same_direction[neighbor_ref] = self.graph[neighbor_ref]

        for node_ref in node_in_same_direction:
            nodes_straightforward = self.continue_straight(node_ref, current_node_ref, usages_number)
            if nodes_straightforward:
                possible_ways.update(nodes_straightforward)

        possible_ways.update(node_in_same_direction)

        return possible_ways

    def find_possible_way(self, current_node_ref, prev_node_ref, figure_element):
        # Return the nodes in in_graph accessible from point_id, lying in direction and at dist distance from point_id
        current_node = self.graph[current_node_ref]
        new_destinations = {}
        node_in_same_direction = {}
        possible_ways = {}

        for neighbor_ref in current_node['neighbors']:
            is_on_the_same_direction = self.node_direction_check(current_node, self.graph[prev_node_ref],
                                                                 self.graph[neighbor_ref],
                                                                 figure_element["direction"])
            if is_on_the_same_direction:
                node_in_same_direction[neighbor_ref] = self.graph[neighbor_ref]

        for node_ref in node_in_same_direction:
            nodes_straight_forward = self.continue_straight(node_ref, current_node_ref)
            possible_ways.update(nodes_straight_forward)

        possible_ways.update(node_in_same_direction)

        for node_ref in possible_ways:
            distance_to_current_node = distance(current_node["lat"], current_node["lon"],
                                                self.graph[node_ref]["lat"], self.graph[node_ref]["lon"])
            is_in_distance = self.is_in_correct_distance(distance_to_current_node, figure_element["length"])
            if is_in_distance:
                new_destinations[node_ref] = self.graph[node_ref]

        return new_destinations

    def node_direction_check(self, node, prev_node, new_node, direction):
        # Check, if new_node in direction(1=right, -1=left, 2=forward)
        # from vector (prev_node, node) with angle_allowance
        # Using float lon and lat as coordinates

        x1, y1 = rotate(node['x'], node['y'], prev_node['x'], prev_node['y'], (math.pi / 2) * direction)
        ax, ay = rotate(node['x'], node['y'], x1, y1, math.radians(self.angle_allowance / 2))
        bx, by = rotate(node['x'], node['y'], x1, y1, -math.radians(self.angle_allowance / 2))

        return if_point_in_angle(node["x"], node["y"], ax, ay, bx, by,
                                 new_node["x"], new_node["y"])

    def find_figure_way(self, lat, lon):
        # Building figure way from (lat, lon) point
        edge = self.edge
        distance_allowance = self.distance_allowance
        edge_coeffs = [0.3, 0.4, 0.6, 0.5, 0.7, 0.8, 1.2, 1.4]
        allowance_coeffs = [0.4, 0.6, 0.7, 0.8]
        starting_nodes = self.get_start_nodes(lat, lon, 10)
        for start_node_ref in starting_nodes:
            start_nodes = self.find_start_ways(start_node_ref)
            for node in start_nodes:
                print("***")
                self.try_continue_way(self.figure[1:], [start_node_ref, node])

        for edge_coeff in edge_coeffs:
            self.edge = self.edge * edge_coeff
            for allowance_coeff in allowance_coeffs:
                self.distance_allowance = self.distance_allowance * allowance_coeff
                for start_node_ref in starting_nodes:
                    start_nodes = self.find_start_ways(start_node_ref)
                    for node in start_nodes:
                        print("***")
                        self.try_continue_way(self.figure[1:], [start_node_ref, node])

        self.edge = edge  # Restored initial values
        self.distance_allowance = distance_allowance # Restored initial values

    def try_continue_way(self, figure, visited_before):
        # figure is list of direction: int
        if not figure:
            self.ways_found.append(show_way_by_points(visited_before, self.graph))
            # print(show_way_by_points(visited_before, self.graph))
            return visited_before

        current_node = visited_before[-1]
        prev_node = visited_before[-2]

        possible_ways = self.find_possible_way(current_node, prev_node, figure[0])
        if not possible_ways:
            # We have no point to continue the route
            return False

        for node_ref in possible_ways:
            visited = list(visited_before)
            visited.append(node_ref)
            result = self.try_continue_way(figure[1:], visited)
            if result:
                return result

        return False

    def find_start_ways(self, start_node_ref):
        # Function to find ways from the node in any direction
        start_node = self.graph[start_node_ref]
        new_destinations = {}

        for neighbor_ref in start_node['neighbors']:
            distance_to_start_node = distance(start_node["lat"], start_node["lon"],
                                              self.graph[neighbor_ref]["lat"], self.graph[neighbor_ref]["lon"])
            is_in_distance = self.is_in_correct_distance(distance_to_start_node, 1)
            if is_in_distance:
                new_destinations[neighbor_ref] = self.graph[neighbor_ref]

        return new_destinations


def main():

    cfg = configparser.ConfigParser()
    cfg.read(os.path.join(os.path.dirname(__file__), 'config.cfg'))
    city_list_path = cfg.get('INPUT_PATH', 'city_list', fallback='Wrong Config file')

    amazon_access_key_id = cfg.get('DEFAULT', 'aws_access_key_id')
    amazon_secret_key = cfg.get('DEFAULT', 'aws_secret_access_key')
    amazon_bucket_name = cfg.get('DEFAULT', 'aws_s3_bucket')
    city_list = static.load_city_list(city_list_path)
    closest_city = static.find_closest_city(57.12314815338618, 35.4577527073621, city_list)
    print(closest_city)

    city_filepath = '/Static/' + closest_city['country'] + '/' + closest_city['lat'] + closest_city['lng'] +'.pickle'

    session = boto3.Session(aws_access_key_id=amazon_access_key_id, aws_secret_access_key=amazon_secret_key)
    s3 = session.resource('s3')
    obj = s3.Object(amazon_bucket_name, city_filepath)
    obj.load()
    crossroads_pickle = obj.get()['Body'].read()
    crossroads = pickle.loads(crossroads_pickle)
    cl = FigureWayFinder(penis_dict, 2000, 0.5, 45, crossroads)

    cl.find_figure_way(57.12314815338618, 35.4577527073621)
    print(cl.ways_found)


if __name__ == '__main__':
    main()
