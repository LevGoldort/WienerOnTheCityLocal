# coding=utf-8
# Making a walking route looking like a dick.

import wiener

# All Israel file, 83 mb:
israel_osm = "/Users/levgoldort/Downloads/israel-and-palestine-latest.osm.pbf"
# Holon near my house, 2km2:
near_house_osm = "/Users/levgoldort/Downloads/planet_34.762,32.004_34.781,32.015.osm.pbf"
california_osm = "/Users/levgoldort/Downloads/planet_-120.0394,38.8848_-119.9224,38.9521.osm.pbf"
moscow_osm = "/Users/levgoldort/Downloads/planet_37.297,55.608_37.96,55.893.osm.pbf"

w = wiener.GenerateGraphHandler(32.05484684105788, 34.769174207787024, 5000)
w.apply_file(israel_osm, locations=True)

crossroads = w.pick_crossroads()

penis = [-1, 1, 1, -1, 2, 1, 1, 2, -1, 1, 1]
figure = [1, 1]

cl = wiener.FigureWayFinder(penis, 3000, 0.4, 90, crossroads)
cl.find_figure_way(32.05484684105788, 34.769174207787024)

#wiener.find_figure_way(32.05484684105788, 34.769174207787024, crossroads, penis, 3000, 0.3, 90)




