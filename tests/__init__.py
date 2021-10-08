import wiener
import unittest

# All Israel file, 83 mb:
israel_osm = "/Users/levgoldort/Downloads/israel-and-palestine-latest.osm.pbf"
# Holon near my house, 2km2:
near_house_osm = "/Users/levgoldort/Downloads/planet_34.762,32.004_34.781,32.015.osm.pbf"
california_osm = "/Users/levgoldort/Downloads/planet_-120.0394,38.8848_-119.9224,38.9521.osm.pbf"
moscow_osm = "/Users/levgoldort/Downloads/planet_37.297,55.608_37.96,55.893.osm.pbf"


# w = wiener.GenerateGraphHandler(32.05484684105788, 34.769174207787024, 5000)
# w.apply_file(israel_osm, locations=True)
#
# crossroads = w.pick_crossroads()

class TestIsRight(unittest.TestCase):

    def test_horizontal(self):
        self.assertEqual(wiener.is_right(0, 0, 1, 0, 1, 2), 1)

    def test_vertical(self):
        self.assertEqual(wiener.is_right(0, 0, 0, 1, 1, 1), 1)

    def test_negative(self):
        self.assertEqual(wiener.is_right(-1, -1, -2, 0, 0, 0), 1)

    def test_false(self):
        self.assertEqual(wiener.is_right(-1, -1, -2, 0, -4, -4), -1)


unittest.main()

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

# 1cl = wiener.FigureWayFinder(penis_dict, 3000, 0.4, 60, crossroads)
# cl.find_figure_way(32.05484684105788, 34.769174207787024)


# def test_simple_turn():
#     graph = {
#         1: {x: 10, y: 20},
#         2: {x: 20, y: 20},
#         3: {x: 20, y: 40},
#         4: {x: 20, y: 40},
#         5: {x: 20, y: 40},
#     }
#     figure = [1]
#     result = find_figure_way(...)
#     self.assertEquals(result, [1, 2, 3])
#
#
# def test_sqrt():
#     a = 2
#     b = 4
#     self.assertEquals(sqrt(4), a)
#     if sqrt(4) == a:
#         print("Success")
#     else:
#         print("Failure")
