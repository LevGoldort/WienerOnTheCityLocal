import osmium
import math
import logging

NAME_EN_TAG = "name:en"
STREET_HIGHWAY_TAGS = frozenset([
    "service",
    "path"
])

DIRECTION_RIGHT = 1
DIRECTION_LEFT = -1

logging.basicConfig(filename='../figure_way_finder.log', encoding='utf-8', level=logging.DEBUG)


def point_in_rect(lat, lon, rect):  # OBSOLETE
    return (rect[0] < lat < rect[1]) and (rect[2] < lon < rect[3])


def rotate(ox, oy, px, py, angle):
    """
    Rotate a point counterclockwise by a given angle around a given origin.

    The angle should be given in radians.

    For clockwise - angle should be negated
    https://stackoverflow.com/questions/34372480/rotate-point-about-another-point-in-degrees-python/34374437
    """

    qx = ox + math.cos(angle) * (px - ox) - math.sin(angle) * (py - oy)
    qy = oy + math.sin(angle) * (px - ox) + math.cos(angle) * (py - oy)
    return qx, qy


def distance(lat0, lon0, lat1, lon1):
    # Return distance in meters between two dots
    # https://stackoverflow.com/questions/639695/how-to-convert-latitude-or-longitude-to-meters
    earth_radius = 6378.137
    d_lat = lat1 * math.pi / 180 - lat0 * math.pi / 180
    d_lon = lon1 * math.pi / 180 - lon0 * math.pi / 180
    a = math.sin(d_lat / 2) ** 2 + math.cos(lat0 * math.pi / 180) * math.cos(lat1 * math.pi / 180) \
        * math.sin(d_lon / 2) ** 2
    c = 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))

    return earth_radius * c * 1000


def generate_set_of_way_ids(point):  # #OBSOLETE
    # Transform ways list of OSM object to Set.
    set_point_ways = set()
    for i in point["ways"]:
        for key in i.keys():
            set_point_ways.add(key)
    return set_point_ways


def vector_cross_product(ax, ay, az, bx, by, bz):  # OBSOLETE
    return [ay*bz-az*by, az*bx-ax*bz, ax*by-ay*bx]


def point_direction(x1, y1, x2, y2, x, y):
    # Checking the direction of a point (x,y) from vector ((x1, y1), (x2, y2))
    if (x2 - x1) * (y - y1) - (y2 - y1) * (x - x1) >= 0:
        return 1  # one direction or in lane
    return -1  # another direction


def sign(x):
    if x >= 0:
        return 1
    return -1


def is_right(x1, y1, x2, y2, x, y):
    # Checking if point (x,y) is to the right from the vector((x1,y1),(x2,y2))
    point_dir = point_direction(x1, y1, x2, y2, x, y)

    if (x2 - x1) != 0:
        a = (y2 - y1) / (x2 - x1)  # y = a * x + b
        d_x = sign(a) * sign(x2 - x1)
    else:
        d_x = sign(y2 - y1)

    d_y = 0
    if y2 - y1 == 0:
        d_y = sign(x1 - x2)  # if the line is horizontal, d_y will be used.
    # (x2 + d_x, y2 + d_y) is a point that definitely lies to the right of the line.
    defined_point_dir = point_direction(x1, y1, x2, y2, x2 + d_x, y2 + d_y)  # Direction of a point to the right

    if point_dir == defined_point_dir:
        return DIRECTION_RIGHT
    return DIRECTION_LEFT


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
        self.point_lat = lat
        self.point_lon = lon
        self.radius = rad

    def way(self, w):
        street_tag = get_street_tag(w.tags)
        if not street_tag:
            return
        for node in w.nodes:
            if distance(self.point_lat, self.point_lon, node.lat, node.lon) < self.radius:
                if node.ref not in self.all_way_dots.keys():
                    self.all_way_dots[node.ref] = {
                        "lat": node.lat,
                        "lon": node.lon,
                        "x": node.x,
                        "y": node.y
                    }

                if "ways" not in self.all_way_dots[node.ref]: #TODO: Create ways on prev setp;
                    self.all_way_dots[node.ref]["ways"] = {}
                self.all_way_dots[node.ref]["ways"][w.id] = w.tags[street_tag]

    def pick_crossroads(self):
        crossroads = {}
        for node_ref in self.all_way_dots:
            if len(self.all_way_dots[node_ref]["ways"]) > 1:
                crossroads[node_ref] = self.all_way_dots[node_ref]
        return crossroads


class FigureWayFinder:

    def __init__(self, figure, perimeter, distance_allowance, angle_allowance, graph):
        self.figure = figure
        self.edge = perimeter / len(figure)
        self.distance_allowance = distance_allowance
        self.angle_allowance = angle_allowance
        self.graph = graph
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

    def is_in_correct_distance(self, distance_to_current_node, length):
        return (length * self.edge * self.distance_allowance
                < distance_to_current_node
                < length * self.edge * (2 - self.distance_allowance))

    def continue_straight(self, current_node_ref, prev_node_ref, usages_number):
        logging.debug("Continue straight called in direction from {} to {}, step {}".format(prev_node_ref, current_node_ref, usages_number))
        if usages_number > 3:
            return None
        usages_number += 1

        graph = dict(self.graph)
        current_node = graph.pop(current_node_ref)
        prev_node = graph.pop(prev_node_ref)
        possible_ways = {}
        node_in_same_direction = {}
        set_current_node_ways = set(current_node["ways"].keys())

        for node_ref in graph:
            set_node_ways = set(graph[node_ref]["ways"].keys())  # List of the way ids of node
            is_on_the_same_way = set_current_node_ways.intersection(set_node_ways)
            is_on_the_same_direction = self.node_direction_check(current_node, prev_node,
                                                                 graph[node_ref], 2)
            distance_to_current_node = distance(current_node["lat"], current_node["lon"],
                                                graph[node_ref]["lat"], graph[node_ref]["lon"])
            if is_on_the_same_way and is_on_the_same_direction and distance_to_current_node > self.edge / 4:
                node_in_same_direction[node_ref] = graph[node_ref]

        for node_ref in node_in_same_direction:
            nodes_straightforward = self.continue_straight(node_ref, current_node_ref, usages_number)
            if nodes_straightforward:
                possible_ways.update(nodes_straightforward)

        possible_ways.update(node_in_same_direction)
        logging.debug("Continue straight called in direction from {} to {}, nodes returned:".format(prev_node_ref, current_node_ref))
        logging.debug(possible_ways)
        return possible_ways

    def find_possible_way(self, current_node_ref, prev_node_ref, figure_element):
        # Return the nodes in in_graph accessible from point_id, lying in direction and at dist distance from point_id
        logging.debug("find_possible_way called to find way from node {} to {} in direction {}".format(prev_node_ref, current_node_ref, figure_element["direction"]))
        graph = dict(self.graph)
        current_node = graph.pop(current_node_ref)
        # Is it better to add check for the cycle instead of copying the graph?
        new_destinations = {}
        set_current_node_ways = set(current_node["ways"].keys())
        node_in_same_direction = {}
        possible_ways = {}

        for node_ref in graph:
            set_node_ways = set(graph[node_ref]["ways"].keys())  # List of the way ids of node
            is_on_the_same_way = set_current_node_ways.intersection(set_node_ways)
            is_on_the_same_direction = self.node_direction_check(current_node, graph[prev_node_ref], graph[node_ref],
                                                                 figure_element["direction"])
            if is_on_the_same_way and is_on_the_same_direction:
                node_in_same_direction[node_ref] = graph[node_ref]

        for node_ref in node_in_same_direction:
            nodes_straight_forward = self.continue_straight(node_ref, current_node_ref, 0)
            possible_ways.update(nodes_straight_forward)

        possible_ways.update(node_in_same_direction)

        for node_ref in possible_ways:
            distance_to_current_node = distance(current_node["lat"], current_node["lon"],
                                                graph[node_ref]["lat"], graph[node_ref]["lon"])
            is_in_distance = self.is_in_correct_distance(distance_to_current_node, figure_element["length"])
            if is_in_distance:
                new_destinations[node_ref] = graph[node_ref]
        logging.debug("find_possible_way called to find way from node {} to {} in direction {}, ways found:".format(prev_node_ref, current_node_ref, figure_element["direction"]))
        logging.debug(new_destinations)
        return new_destinations

    def node_direction_check(self, node, prev_node, new_node, direction):
        # Check, if new_node in direction(1=right, -1=left, 2=forward)
        # from vector (prev_node, node) with angle_allowance
        # Using integer lon and lat as coordinates
        # TODO : fix first part of the func, using rotate instead of this hard shit

        Radius = math.sqrt((prev_node["x"] - node["x"]) ** 2  # Distance between point and prev in coords
                           + (prev_node["y"] - node["y"]) ** 2)

        if direction != 2:

            cos = (prev_node["x"] - node["x"]) / Radius
            alfa = math.acos(cos)  # Angle between line point-prev_point and abscissa

            sign = is_right(node["x"], node["y"],
                            node["x"] + Radius, node["y"],
                            prev_node["x"], prev_node["y"])


            # Sign indicates, if slope is positive or not. If prev_point above abscissa, it is to the right of it,
            # and slope is positive.

            beta1 = direction * math.pi / 2 + sign * alfa - math.radians(self.angle_allowance / 2)  # Deflection left
            beta2 = direction * math.pi / 2 + sign * alfa + math.radians(self.angle_allowance / 2)  # Deflection right

        # pi/2= right, -pi/2 = left, pi = forward.

            ax = node["x"] + Radius * math.cos(beta1)
            ay = node["y"] + Radius * math.sin(beta1)
            bx = node["x"] + Radius * math.cos(beta2)
            by = node["y"] + Radius * math.sin(beta2)

        else:
            x1 = 2 * node['x'] - prev_node['x']
            y1 = 2 * node['y'] - prev_node['y']
            ax, ay = rotate(node['x'], node['y'], x1, y1, math.radians(self.angle_allowance / 2))
            bx, by = rotate(node['x'], node['y'], x1, y1, -math.radians(self.angle_allowance / 2))

        # Two points A and B forming angle_allowance from the point to direction

        return if_point_in_angle(node["x"], node["y"], ax, ay, bx, by,
                                 new_node["x"], new_node["y"])

    def find_figure_way(self, lat, lon):
        # Building figure way from (lat, lon) point
        logging.debug("find_figure_way called from lat {}, lon {}".format(lat, lon))
        start_node_ref = self.get_start_node(lat, lon)
        start_nodes = self.find_start_ways(start_node_ref)
        for node in start_nodes:
            print("***")
            self.try_continue_way(self.figure[1:], [start_node_ref, node])

    def try_continue_way(self, figure, visited_before):
        # figure is list of direction: int
        logging.debug("try_continue_way called. current node is {}, prev node is {} visited before: {}, current direction:{}".format(visited_before[-1], visited_before[-2], visited_before, figure[0]["direction"]))
        if not figure:
            return visited_before

        current_node = visited_before[-1]
        prev_node = visited_before[-2]

        possible_ways = self.find_possible_way(current_node, prev_node, figure[0])
        logging.debug("try_continue_way is back. Current node is {}, prev node is {} visited before: {}, current direction:{}, possible ways found:".format(visited_before[-1], visited_before[-2], visited_before, figure[0]["direction"]))
        logging.debug(possible_ways)
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
        logging.debug("find_start_ways called from node {}".format(start_node_ref))
        graph = dict(self.graph)
        start_node = graph.pop(start_node_ref)
        new_destinations = {}
        set_start_node_ways = set(start_node["ways"].keys())

        for node_ref in graph:
            set_node_ways = set(graph[node_ref]["ways"].keys())  # List of the way ids of node
            distance_to_start_node = distance(start_node["lat"], start_node["lon"],
                                              graph[node_ref]["lat"], graph[node_ref]["lon"])
            is_on_the_same_way = set_start_node_ways.intersection(set_node_ways)
            is_in_distance = self.is_in_correct_distance(distance_to_start_node, 1)
            if is_in_distance and is_on_the_same_way:
                new_destinations[node_ref] = graph[node_ref]
        logging.debug("find_start_ways  from node {} found these ways:".format(start_node_ref))
        logging.debug(new_destinations)
        return new_destinations
