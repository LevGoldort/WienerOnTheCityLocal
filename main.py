# coding=utf-8
# Making a walking route looking like a dick.

import weiner

# All Israel file, 83 mb:
israel_osm = "/Users/levgoldort/Downloads/israel-and-palestine-latest.osm.pbf"
# Holon near my house, 2km2:
near_house_osm = "/Users/levgoldort/Downloads/planet_34.762,32.004_34.781,32.015.osm.pbf"
california_osm = "/Users/levgoldort/Downloads/planet_-120.0394,38.8848_-119.9224,38.9521.osm.pbf"

w = weiner.GenerateGraphHandler(32.05496079307, 34.768906802947434, 5000)
w.apply_file(israel_osm, locations=True)

crossroads = w.pick_crossroads()

penis = [-1, 1, 1, -1, 2, 1, 1, 2, -1, 1, 1]
figure = [1, 1, 1]

# Weiner_lib.print_point_links(damn)

weiner.bootstrap(32.05496079307, 34.768906802947434, crossroads, figure, 1000, 0.4, 60)

