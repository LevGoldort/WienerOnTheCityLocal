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


def is_street(tags):
    # Check OSM way tags to decide if it is a street
    if "name:en" in tags:
        return "name:en"
    if ("highway" in tags) and (tags["highway"] in ("service", "path")):
        return "highway"
    return False


class GenerateGraphHandler(osmium.SimpleHandler):

    # Generates a graph of crossroads in radius in meters around the point (lat, lon)

    def __init__(self, lat, lon, rad):
        osmium.SimpleHandler.__init__(self)
        self.all_way_dots = {}
        self.point_lat = lat
        self.point_lon = lon
        self.radius = rad

    def way(self, w):
        street_tag = is_street(w.tags)
        if street_tag:
            for node in w.nodes:
                if distance(self.point_lat, self.point_lon, node.lat, node.lon) < self.radius:
                    if node.ref not in self.all_way_dots.keys():
                        self.all_way_dots[node.ref] = {}
                        self.all_way_dots[node.ref]["lat"] = node.lat
                        self.all_way_dots[node.ref]["lon"] = node.lon
                        self.all_way_dots[node.ref]["x"] = node.x
                        self.all_way_dots[node.ref]["y"] = node.y

                    if "ways" not in self.all_way_dots[node.ref].keys():
                        self.all_way_dots[node.ref]["ways"] = []
                    self.all_way_dots[node.ref]["ways"].append({str(w.id): w.tags[street_tag]})

    def pick_crossroads(self):
        crossroads = {}
        for node in self.all_way_dots.keys():
            if len(self.all_way_dots[node]["ways"]) > 1:
                crossroads[node] = self.all_way_dots[node]
        return crossroads


def is_right(x1, y1, x2, y2, x, y):
    # Checking if point (x,y) is to the right from the line((x1,y1),(x2,y2))
    if ((x2 - x1) * (y - y1) - (y2 - y1) * (x - x1)) > 0:
        return 1  # 1=right
    return -1  # -1=left


def get_start_point(lat, lon, graph):
    min_rad = 50000
    min_point_id = 0

    for node in graph:
        new_rad = distance(lat, lon, graph[node]["lat"], graph[node]["lon"])
        if new_rad < min_rad:
            min_rad = new_rad
            min_point_id = node
    return min_point_id


def generate_set_of_way_ids(point):
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


def find_possible_way(point_id, prev_point_id, direction, dist, distance_allowance,
                      angle_allowance, in_graph):
    graph = dict(in_graph)
    point = in_graph[point_id]
    graph.pop(point_id)
    new_destinations = {}
    set_point_ways = generate_set_of_way_ids(point)

    for node in graph:

        set_node_ways = generate_set_of_way_ids(graph[node])  # List of the way ids of node
        point_node_intersection_ways = set_point_ways.intersection(set_node_ways)
        point_node_distance = distance(point["lat"], point["lon"], graph[node]["lat"], graph[node]["lon"])

        if point_node_intersection_ways \
                and point_direction_check(point_id, prev_point_id, node, direction, angle_allowance, in_graph) \
                and dist * distance_allowance < point_node_distance < dist / distance_allowance:
            # node lies on the same way as point_id on proper direction and in proper distance
            new_destinations[node] = graph[node]

    return new_destinations


def point_direction_check(point_id, prev_point_id, new_point_id, direction, angle_allowance, graph):
    # Check, if new_point_id in direction(1=right, -1=left, 2=forward)
    # from vector (prev_point_id, point_id) with angle_allowance
    # Using integer lon and lat as coordinates

    R = math.sqrt((graph[prev_point_id]["x"] - graph[point_id]["x"]) ** 2  # Distance between point and prev in coords
                  + (graph[prev_point_id]["y"] - graph[point_id]["y"]) ** 2)

    cos = (graph[prev_point_id]["x"] - graph[point_id]["x"]) / R
    alfa = math.acos(cos)  # Angle between line point-prev_point and abscissa

    sign = is_right(graph[point_id]["x"], graph[point_id]["y"],
                    graph[point_id]["x"] + R, graph[point_id]["y"],
                    graph[prev_point_id]["x"], graph[prev_point_id]["y"])

    # Sign indicates, if slope is positive or not. If prev_point above abscissa, it is to the right of it,
    # and slope is positive.

    beta1 = direction * math.pi / 2 + sign * alfa - math.radians(angle_allowance / 2)  # Deflection left
    beta2 = direction * math.pi / 2 + sign * alfa + math.radians(angle_allowance / 2)  # Deflection right

    # pi/2= right, -pi/2 = left, pi = forward.

    ax = graph[point_id]["x"] + R * math.cos(beta1)
    ay = graph[point_id]["y"] + R * math.sin(beta1)
    bx = graph[point_id]["x"] + R * math.cos(beta2)
    by = graph[point_id]["y"] + R * math.sin(beta2)

    # Two points A and B forming angle_allowance from the point to direction

    return if_point_in_angle(graph[point_id]["x"], graph[point_id]["y"], ax, ay, bx, by,
                             graph[new_point_id]["x"], graph[new_point_id]["y"])


def show_way_by_points(points, graph):
    # Test function to make a way visual. Returns link to Google Maps route
    address = "https://www.google.com/maps/dir/"
    for point in points:
        point_str = str(graph[point]["lat"])+","+str(graph[point]["lon"])+"/"
        address = address + point_str
    return address


def bootstrap(lat, lon, in_graph, figure, perimeter, distance_allowance, angle_allowance):
    point = get_start_point(lat, lon, in_graph)
    edge = perimeter / len(figure)
    start_points = find_start_ways(point, in_graph, edge, distance_allowance)
    print("start:", "https://www.google.com/maps/search/?api=1&query=" + str(in_graph[point]["lat"]) + "%2C" + str(
        in_graph[point]["lon"]))
    for node in start_points:
        print("***")
        find_figure_way(node, point, figure[1:], edge, in_graph, distance_allowance, angle_allowance, [point, node])
        # if isinstance(result, list):
        #     print(show_way_by_points(result, in_graph))


def find_figure_way(point, prev_point, figure, edge, in_graph, dist_allowance, angle_allowance, visited_before):
    # figure is list of direction: int
    # edge in meters

    if not figure:
        print(show_way_by_points(visited_before, in_graph))
        return visited_before

    graph = dict(in_graph)
    visited = visited_before

    possible_ways = find_possible_way(point, prev_point, figure[0], edge, dist_allowance, angle_allowance, graph)

    if not possible_ways:
        # We have no point to continue the route
        return False

    for node in possible_ways:
        visited.append(node)
        if find_figure_way(node, point, figure[1:], edge, graph, dist_allowance, angle_allowance, visited):
            return True

    return False


def find_start_ways(point_id, in_graph, dist, distance_allowance):
    # Function to find ways from the node in any direction

    graph = dict(in_graph)
    point = in_graph[point_id]
    graph.pop(point_id)
    new_destinations = {}
    set_point_ways = generate_set_of_way_ids(point)
    for node in graph:
        set_node_ways = generate_set_of_way_ids(graph[node])  # List of the way ids of node
        point_node_intersection_ways = set_point_ways.intersection(set_node_ways)
        point_node_distance = distance(point["lat"], point["lon"], graph[node]["lat"], graph[node]["lon"])
        if point_node_intersection_ways \
                and dist * distance_allowance < point_node_distance < dist / distance_allowance:
            new_destinations[node] = graph[node]

    return new_destinations
