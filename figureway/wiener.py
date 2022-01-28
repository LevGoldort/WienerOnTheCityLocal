import math
import logging
import staticmaps

from distance import distance

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


class PointShower:

    def __init__(self):
        self.context = staticmaps.Context()
        self.context.set_tile_provider(staticmaps.tile_provider_OSM)

    def show_point(self, lat, lon, color=staticmaps.RED):
        map_center = staticmaps.create_latlng(lat, lon)
        self.context.add_object(staticmaps.Marker(map_center, color=color, size=10))

    def show_points_on_map(self, graph, point, points_list, second_points_list=None):
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


def if_point_in_angle(ax, ay, bx, by, cx, cy, x, y):
    # a function to check if x,y in angle formed by 3 points A, B, C.
    # https://math.stackexchange.com/questions/1470784/find-if-a-point-lies-within-the-angle-formed-by-three-other-points

    j = ((y - ay) * (bx - ax) - (by - ay) * (x - ax)) \
        / ((cy - ay) * (bx - ax) - (by - ay) * (cx - ax))

    i = ((x - ax) - (cx - ax) * j) / (bx - ax)

    if i > 0 and j > 0:
        return True

    return False


def show_way_by_points(points, graph):
    # Test function to make a way visual. Returns link to Google Maps route
    address = "https://www.google.com/maps/dir/"
    for point in points:
        point_str = str(graph[point]["lat"]) + "," + str(graph[point]["lon"]) + "/"
        address = address + point_str
    return address


class FigureWayFinder:

    def __init__(self, figure, perimeter, distance_allowance, angle_allowance, graph):
        self.figure = figure
        self.edge = perimeter / len(figure)
        self.distance_allowance = distance_allowance
        self.angle_allowance = angle_allowance
        self.graph = graph
        self.ways_found = []
        logging.debug("FigureWayFinder initialized with figure {}, perimeter {}".format(figure, perimeter))

    def length_ratio(self, nodes):
        # The function to count ratio of length. Works only with penis_dict, not abstract.
        left_egg_start_node = self.graph[nodes[1]]
        left_egg_end_node = self.graph[nodes[2]]
        penis_start_node = self.graph[nodes[3]]
        penis_end_node = self.graph[nodes[4]]
        left_egg_len = distance(left_egg_start_node['lat'], left_egg_start_node['lon'],
                                left_egg_end_node['lat'], left_egg_end_node['lon'])

        penis_len = distance(penis_start_node['lat'], penis_start_node['lon'],
                             penis_end_node['lat'], penis_end_node['lon'])

        return penis_len / left_egg_len

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
            if is_on_the_same_direction and distance_to_current_node: #> self.edge / 3:
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
        edge_coefficients = [0.7, 0.8, 1.2, 1.4]
        allowance_coefficients = [0.7, 0.8]
        starting_nodes = self.get_start_nodes(lat, lon, 10)
        for start_node_ref in starting_nodes:
            start_nodes = self.find_start_ways(start_node_ref)
            for node in start_nodes:
                print("***")
                self.try_continue_way(self.figure[1:], [start_node_ref, node])

        if self.ways_found:
            return

        for edge_coefficient in edge_coefficients:  # Make weaker coefficients if no ways found.
            self.edge = self.edge * edge_coefficient
            for allowance_coefficient in allowance_coefficients:
                self.distance_allowance = self.distance_allowance * allowance_coefficient
                for start_node_ref in starting_nodes:
                    start_nodes = self.find_start_ways(start_node_ref)
                    for node in start_nodes:
                        print("***")
                        self.try_continue_way(self.figure[1:], [start_node_ref, node])
            if self.ways_found:
                return

        self.edge = edge  # Restored initial values
        self.distance_allowance = distance_allowance  # Restored initial values

    def try_continue_way(self, figure, visited_before):
        # figure is list of direction: int
        if not figure:
            self.ways_found.append({'way': visited_before, 'ratio': self.length_ratio(visited_before)})
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

    def get_best_route(self):
        # Returns the route with biggest length ratio

        ways_sorted = sorted(self.ways_found, key=lambda d: d['ratio'], reverse=True)

        #  best_way_string = show_way_by_points(ways_sorted[0]['way'], self.graph)

        return ways_sorted[0]


def main():
    pass


if __name__ == '__main__':
    main()
