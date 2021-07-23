import osmium
import math


def point_in_rect(lat, lon, rect):
    return (rect[0] < lat < rect[1]) and (rect[2] < lon < rect[3])


def intersection(lst1, lst2):
    return [value for value in lst1 if value in lst2]


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


NAME_EN_TAG = "name:en"
STREET_HIGHWAY_TAGS = frozenset([
    "service",
    "path"
])


def get_street_tag(tags):
    # Check OSM way tags to decide if it is a street
    if "place" in tags:
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

                if "ways" not in self.all_way_dots[node.ref]:
                    self.all_way_dots[node.ref]["ways"] = {}
                self.all_way_dots[node.ref]["ways"][w.id] = w.tags[street_tag]

    def pick_crossroads(self):
        crossroads = {}
        for node_ref in self.all_way_dots:
            if len(self.all_way_dots[node_ref]["ways"]) > 1:
                crossroads[node_ref] = self.all_way_dots[node_ref]
        return crossroads


DIRECTION_RIGHT = 1
DIRECTION_LEFT = -1


def is_right(x1, y1, x2, y2, x, y):
    # Checking if point (x,y) is to the right from the line((x1,y1),(x2,y2))
    if ((x2 - x1) * (y - y1) - (y2 - y1) * (x - x1)) > 0:
        return DIRECTION_RIGHT  # 1=right
    return DIRECTION_LEFT  # -1=left


def get_start_node(lat, lon, graph):
    # Find the closest to (lat, lon) node in graph
    min_distance = 0
    min_point_id = None

    for node_ref in graph:
        node_distance = distance(lat, lon, graph[node_ref]["lat"], graph[node_ref]["lon"])
        if node_distance < min_distance or min_point_id is None:
            min_distance = node_distance
            min_point_id = node_ref
    return min_point_id


def generate_set_of_way_ids(point):  # MAYBE obsolete
    # Transform ways list of OSM object to Set.
    set_point_ways = set()
    for i in point["ways"]:
        for key in i.keys():
            set_point_ways.add(key)
    return set_point_ways


def print_point_links(graph):
    # Test function to print links to points of graph
    for i in graph:
        print(i)
        print("https://www.google.com/maps/search/?api=1&query=" + str(graph[i]["lat"]) + "%2C" + str(
            graph[i]["lon"]))
        print(graph[i]["ways"])


def if_point_in_angle(ax, ay, bx, by, cx, cy, x, y):
    # a function to check if x,y in angle formed by 3 points A, B, C.
    # https://math.stackexchange.com/questions/1470784/find-if-a-point-lies-within-the-angle-formed-by-three-other-points

    j = ((y - ay) * (bx - ax) - (by - ay) * (x - ax)) \
        / ((cy - ay) * (bx - ax) - (by - ay) * (cx - ax))

    i = ((x - ax) - (cx - ax) * j) / (bx - ax)

    if i > 0 and j > 0:
        return True

    return False


def is_in_correct_distance(distance_to_current_node, dist, distance_allowance):
    return dist * distance_allowance < distance_to_current_node < dist * (2 - distance_allowance)


def find_possible_way(current_node_ref, prev_node_ref, direction, dist, distance_allowance,
                      angle_allowance, in_graph):
    # Return the nodes in in_graph accessible from point_id, lying in direction and at dist distance from point_id

    graph = dict(in_graph)
    current_node = graph.pop(current_node_ref)
    new_destinations = {}
    set_current_node_ways = set(current_node["ways"].keys())

    for node in graph:

        set_node_ways = set(graph[node]["ways"].keys())  # List of the way ids of node
        distance_to_current_node = distance(current_node["lat"], current_node["lon"],
                                            graph[node]["lat"], graph[node]["lon"])
        is_on_the_same_way = set_current_node_ways.intersection(set_node_ways)
        is_on_the_same_direction = node_direction_check(current_node, graph[prev_node_ref], graph[node],
                                                        direction, angle_allowance)
        is_in_distance = is_in_correct_distance(distance_to_current_node, dist, distance_allowance)

        if is_on_the_same_way and is_on_the_same_direction and is_in_distance:
            # node lies on the same way as point_id on proper direction and in proper distance
            new_destinations[node] = graph[node]

    return new_destinations


def node_direction_check(node, prev_node, new_node, direction, angle_allowance):
    # Check, if new_node in direction(1=right, -1=left, 2=forward)
    # from vector (prev_node, node) with angle_allowance
    # Using integer lon and lat as coordinates

    Radius = math.sqrt((prev_node["x"] - node["x"]) ** 2  # Distance between point and prev in coords
                       + (prev_node["y"] - node["y"]) ** 2)

    cos = (prev_node["x"] - node["x"]) / Radius
    alfa = math.acos(cos)  # Angle between line point-prev_point and abscissa

    sign = is_right(node["x"], node["y"],
                    node["x"] + Radius, node["y"],
                    prev_node["x"], prev_node["y"])

    # Sign indicates, if slope is positive or not. If prev_point above abscissa, it is to the right of it,
    # and slope is positive.

    beta1 = direction * math.pi / 2 + sign * alfa - math.radians(angle_allowance / 2)  # Deflection left
    beta2 = direction * math.pi / 2 + sign * alfa + math.radians(angle_allowance / 2)  # Deflection right

    # pi/2= right, -pi/2 = left, pi = forward.

    ax = node["x"] + Radius * math.cos(beta1)
    ay = node["y"] + Radius * math.sin(beta1)
    bx = node["x"] + Radius * math.cos(beta2)
    by = node["y"] + Radius * math.sin(beta2)

    # Two points A and B forming angle_allowance from the point to direction

    return if_point_in_angle(node["x"], node["y"], ax, ay, bx, by,
                             new_node["x"], new_node["y"])


def show_way_by_points(points, graph):
    # Test function to make a way visual. Returns link to Google Maps route
    address = "https://www.google.com/maps/dir/"
    for point in points:
        point_str = str(graph[point]["lat"]) + "," + str(graph[point]["lon"]) + "/"
        address = address + point_str
    return address


def find_figure_way(lat, lon, in_graph, figure, perimeter, distance_allowance, angle_allowance):
    # Building figure way from (lat, lon) point
    start_node_ref = get_start_node(lat, lon, in_graph)
    edge = perimeter / len(figure)
    start_nodes = find_start_ways(start_node_ref, in_graph, edge, distance_allowance)

    for node in start_nodes:
        print("***")
        try_continue_way(figure[1:], edge, in_graph, distance_allowance, angle_allowance, [start_node_ref, node])


def try_continue_way(figure, edge, in_graph, distance_allowance, angle_allowance, visited_before):
    # figure is list of direction: int
    # edge in meters

    if not figure:
        print(show_way_by_points(visited_before, in_graph))
        return visited_before

    current_node = visited_before[-1]
    prev_node = visited_before[-2]

    possible_ways = find_possible_way(current_node, prev_node, figure[0], edge,
                                      distance_allowance, angle_allowance, in_graph)

    if not possible_ways:
        # We have no point to continue the route
        return False

    for node_ref in possible_ways:
        visited = list(visited_before)
        visited.append(node_ref)
        result = try_continue_way(figure[1:], edge, in_graph, distance_allowance, angle_allowance, visited)
        if result:
            return result

    return False


def find_start_ways(start_node_ref, in_graph, dist, distance_allowance):
    # Function to find ways from the node in any direction

    graph = dict(in_graph)
    start_node = graph.pop(start_node_ref)
    new_destinations = {}
    set_start_node_ways = set(start_node["ways"].keys())

    for node_ref in graph:
        set_node_ways = set(graph[node_ref]["ways"].keys())  # List of the way ids of node
        distance_to_start_node = distance(start_node["lat"], start_node["lon"],
                                          graph[node_ref]["lat"], graph[node_ref]["lon"])
        is_on_the_same_way = set_start_node_ways.intersection(set_node_ways)
        is_in_distance = is_in_correct_distance(distance_to_start_node, dist, distance_allowance)
        if is_in_distance and is_on_the_same_way:
            new_destinations[node_ref] = graph[node_ref]

    return new_destinations
