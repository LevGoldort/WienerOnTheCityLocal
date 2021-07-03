# coding=utf-8
# Making a walking route looking like a dick.

import osmium, pyatlas

hand_drawn_penis = [[0, 0], [-4, 0], [-12, 4], [-14, 9], [-12, 12], [-10, 13], [-5, 13], [-2, 11], [-2, 26], [-1, 29],
                    [2, 29], [3, 26], [3, 11], [6, 13], [11, 13], [14, 12], [16, 8], [14, 4], [7, 0], [0, 0]]
# All Israel file, 83 mb:
IsrPalOsm = "/Users/levgoldort/Downloads/israel-and-palestine-latest.osm.pbf"
# Holon near my house, 2km2:
Holon_osm = "/Users/levgoldort/Downloads/planet_34.762,32.004_34.781,32.015.osm.pbf"


def dist(p, q):
    return ((p[0] - q[0]) ** 2 + (p[1] - q[1]) ** 2) ** 0.5

const_rect = [
    32.004,
    32.009,
    34.759,
    34.765]

def Pointinrect(lat, lon, rect):
    if (rect[0] < lat < rect[1]) and (rect[2] < lon < rect[3]):
        return True
    else:
        return False

def intersection(lst1, lst2):
    lst3 = [value for value in lst1 if value in lst2]
    return lst3

class HolonHandler(osmium.SimpleHandler):

# Get all the nodes in rectangle

    def __init__(self, rect):
        osmium.SimpleHandler.__init__(self)
        self.rect = rect
        self.num_nodes = 0
        self.nodes_names = []

    def node(self, n):
        if Pointinrect(n.location.lat, n.location.lon, self.rect):
            self.num_nodes += 1
            self.nodes_names.append(n.id)

class WayHandler(osmium.SimpleHandler):

#Get all ways that have their nodes in list of nodes

    def __init__(self, list_of_nodes):
        osmium.SimpleHandler.__init__(self)
        self.set_of_nodes = list_of_nodes
        self.arrayofways = []

    def way(self, w):
        node_ref_list = [value.ref for value in w.nodes] #w.nodes[i]ref = integer node id
        elements = {}
        if intersection(self.set_of_nodes, node_ref_list):
            if 'name:en' in w.tags:
                elements['way_name'] = w.tags['name:en']
                elements["way_nodes"] = node_ref_list
                elements['way_id'] = w.id
                self.arrayofways.append(elements)

class WayIntersectionHandler(osmium.SimpleHandler):

    def __init__(self, waytocheck):
        osmium.SimpleHandler.__init__(self)
        self.waytocheck = waytocheck
        self.intersections = []

    def way(self, w):
        node_ref_list = [value.ref for value in w.nodes] #w.nodes[i]ref = integer node id
        intersected_nodes = intersection(node_ref_list, self.waytocheck["way_nodes"])
        element = {}
        if intersected_nodes and 'name:en' in w.tags and self.waytocheck['way_id'] != w.id:
            element['way1'] = w.tags['name:en']
            element['way2'] = self.waytocheck['way_name']
            element['node_list'] = intersected_nodes
            self.intersections.append(element)



h = HolonHandler(const_rect)
h.apply_file(Holon_osm)

w = WayHandler(h.nodes_names)
w.apply_file(Holon_osm)

print w.arrayofways

d = WayIntersectionHandler(w.arrayofways[0])
d.apply_file(Holon_osm)

print d.intersections
