# # coding=utf-8
# # Making a walking route looking like a dick.
#
import figureway.wiener as wiener
import time
import unittest
import pickle

#
# All Israel file, 83 mb:
israel_osm = "/Users/levgoldort/Downloads/israel-and-palestine-latest.osm.pbf"
# Holon near my house, 2km2:
near_house_osm = "/Users/levgoldort/Downloads/planet_34.762,32.004_34.781,32.015.osm.pbf"
california_osm = "/Users/levgoldort/Downloads/planet_-120.0394,38.8848_-119.9224,38.9521.osm.pbf"
moscow_osm = "/Users/levgoldort/Downloads/planet_36.16,54.7_39.91,56.27.osm.pbf"
tel_aviv_osm = "/Users/levgoldort/Downloads/planet_34.683,31.975_34.986,32.166.osm.pbf"

w = wiener.GenerateGraphHandler(55.75520476225699, 37.6482829474615, 5000)
t = time.time()
w.apply_file(israel_osm, locations=True)
d = time.time() - t

print('executed in', d)

crossroads = w.pick_crossroads()
with open('filename.pickle', 'wb') as handle:
    pickle.dump(crossroads, handle, protocol=pickle.HIGHEST_PROTOCOL)
t = time.time()
with open('filename.pickle', 'rb') as handle:
    crossroads = pickle.load(handle)


d = time.time() - t
print('executed in', d)
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

figure_dict = penis_dict

cl = wiener.FigureWayFinder(figure=figure_dict, perimeter=2000, distance_allowance=0.5, angle_allowance=45,graph=crossroads)
cl.find_figure_way(55.75520476225699, 37.6482829474615)

for element in cl.ways_found:
    print(element)
#
# nodes = cl.get_start_nodes(32.00665858608871, 34.76279565935689, 5)
#
# wiener.show_points_on_map(crossroads, nodes[0], nodes[1:])
