# # coding=utf-8
# # Making a walking route looking like a dick.
#
import figureway.wiener as wiener
import time
import unittest
#
# All Israel file, 83 mb:
israel_osm = "/Users/levgoldort/Downloads/israel-and-palestine-latest.osm.pbf"
# Holon near my house, 2km2:
near_house_osm = "/Users/levgoldort/Downloads/planet_34.762,32.004_34.781,32.015.osm.pbf"
california_osm = "/Users/levgoldort/Downloads/planet_-120.0394,38.8848_-119.9224,38.9521.osm.pbf"
moscow_osm = "/Users/levgoldort/Downloads/planet_37.297,55.608_37.96,55.893.osm.pbf"
tel_aviv_osm = "/Users/levgoldort/Downloads/planet_34.683,31.975_34.986,32.166.osm.pbf"
#
w = wiener.GenerateGraphHandler(32.054905164244, 34.768934711842135, 900)
w.apply_file(tel_aviv_osm, locations=True)
crossroads = w.pick_crossroads()
#
# penis = [-1, 1, 1, -1, 2, 1, 1, 2, -1, 1, 1]
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
#
# figure = [1, 1]
#
# figure_dict = [{"direction": -1, "length": 1},
#                {"direction": 1, "length": 1},
#                {"direction": 1, "length": 1}]
#
#
# cl = wiener.FigureWayFinder(figure_dict, 500, 0.4, 45, crossroads)
#
# start_time = time.time()
# cl.find_figure_way(32.05484142187112, 34.77018704477493)
# print("executed in", time.time() - start_time)
#
# print(cl.node_direction_check(crossroads[2470035551], crossroads[2470035547], crossroads[540429611], 1))

years = [2011 + element for element in range(0, 10)]
print(years)