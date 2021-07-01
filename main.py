# coding=utf-8
# Making a walking route looking like a dick.

import osmium, pyatlas

GoogleApikey = "AIzaSyCslQhPc_O-f4AGULu66AUcE_ORA0C9kJw"

hand_drawn_penis = [[0, 0], [-4, 0], [-12, 4], [-14, 9], [-12, 12], [-10, 13], [-5, 13], [-2, 11], [-2, 26], [-1, 29],
                    [2, 29], [3, 26], [3, 11], [6, 13], [11, 13], [14, 12], [16, 8], [14, 4], [7, 0], [0, 0]]

IsrPalOsm = "/Users/levgoldort/Downloads/israel-and-palestine-latest.osm.pbf"
Holon_osm = "/Users/levgoldort/Downloads/planet_34.762,32.004_34.781,32.015.osm.pbf"


def dist(p, q):
    return ((p[0] - q[0]) ** 2 + (p[1] - q[1]) ** 2) ** 0.5

rect = [
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
    if lst3 != []:
        return True
    else:
        return False

class HolonHandler(osmium.SimpleHandler):
    def __init__(self):
        osmium.SimpleHandler.__init__(self)
        self.num_nodes = 0
        self.nodes_names = []

    def node(self, n):
        if Pointinrect(n.location.lat, n.location.lon, rect):
            self.num_nodes += 1
            self.nodes_names.append(n.id)

class HolonWayHandler(osmium.SimpleHandler):
    def __init__(self, list_of_nodes):
        osmium.SimpleHandler.__init__(self)
        self.nodes_names = []
        self.waynumber = 0
        self.set_of_nodes = list_of_nodes

    def way(self, w):
        node_ref_list = [value.ref for value in w.nodes]
        if intersection(self.set_of_nodes, node_ref_list):
            self.waynumber += 1
            if 'name' in w.tags:
                print w.tags['name']
                self.nodes_names.append(w.id)

class HolonWayIntersectionHandler(osmium.SimpleHandler):
    def __init__(self, list_of_nodes):
        osmium.SimpleHandler.__init__(self)
        self.nodes_names = []
        self.waynumber = 0
        self.set_of_nodes = list_of_nodes



h = HolonHandler()
h.apply_file(Holon_osm)

print("Number of nodes: %d" % h.num_nodes)
print(h.nodes_names)

w = HolonWayHandler(h.nodes_names)
w.apply_file(Holon_osm)

print w.nodes_names