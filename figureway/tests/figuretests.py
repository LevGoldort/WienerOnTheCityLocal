import os, sys, unittest

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
# https://stackoverflow.com/questions/16780014/import-file-from-parent-directory

import wiener

# All Israel file, 83 mb:
israel_osm = "/Users/levgoldort/Downloads/israel-and-palestine-latest.osm.pbf"

# Holon near my house, 2km2:
near_house_osm = "/Users/levgoldort/Downloads/planet_34.762,32.004_34.781,32.015.osm.pbf"
california_osm = "/Users/levgoldort/Downloads/planet_-120.0394,38.8848_-119.9224,38.9521.osm.pbf"
moscow_osm = "/Users/levgoldort/Downloads/planet_37.297,55.608_37.96,55.893.osm.pbf"


class TestIsRight(unittest.TestCase):

    def test_horizontal(self):
        self.assertEqual(wiener.is_right(0, 0, 1, 0, 1, 2), -1)

    def test_vertical(self):
        self.assertEqual(wiener.is_right(0, 0, 0, 1, 1, 1), 1)

    def test_negative(self):
        self.assertEqual(wiener.is_right(-1, -1, -2, 0, 0, 0), 1)

    def test_false(self):
        self.assertEqual(wiener.is_right(-1, -1, -2, 0, -4, -4), -1)


# Crossroads in Florentin, Tel Aviv:


A = {'x': 320587653, 'y': 347698838}  # KISHON / MATALON
B = {'x': 320588007, 'y': 347702842}  # MATALON / GILADI
C = {'x': 320580717, 'y': 347704126}  # WOLFSON / GILADI (to the right from AB, 90deg)
D = {'x': 320580247, 'y': 347699899}  # WOLFSOM / KISHON (to the right from AB, 110deg)
E = {'x': 320581673, 'y': 347715051}  # WOLFSON / HASHUK (to the right but far away)
F = {'x': 320587125, 'y': 347694584}  # MIZRAHI / MATALON (on AB, FAB)
G = {'x': 320588484, 'y': 347707568}  # HERZL / MATALON (on AB, ABG)


class TestNodeDirectionCheck(unittest.TestCase):

    def test_1(self):
        wayfinder = wiener.FigureWayFinder([{"direction": -1, "length": 1}], 2000, 0.5, 30, {})
        self.assertEqual(wayfinder.node_direction_check(A, B, C, 1), False)

    def test_2(self):
        wayfinder = wiener.FigureWayFinder([{"direction": -1, "length": 1}], 2000, 0.5, 40, {})
        self.assertEqual(wayfinder.node_direction_check(B, A, C, 1), True)

    def test_3(self):
        wayfinder = wiener.FigureWayFinder([{"direction": -1, "length": 1}], 2000, 0.5, 15, {})
        self.assertEqual(wayfinder.node_direction_check(B, A, D, 1), False)

    def test_4(self):
        wayfinder = wiener.FigureWayFinder([{"direction": -1, "length": 1}], 2000, 0.5, 90, {})
        self.assertEqual(wayfinder.node_direction_check(B, A, D, 1), True)

    def test_5(self):
        wayfinder = wiener.FigureWayFinder([{"direction": -1, "length": 1}], 2000, 0.5, 90, {})
        self.assertEqual(wayfinder.node_direction_check(B, A, E, 1), False)

    def test_6(self):
        wayfinder = wiener.FigureWayFinder([{"direction": -1, "length": 1}], 2000, 0.5, 160, {})
        self.assertEqual(wayfinder.node_direction_check(B, A, E, 1), True)

    def test_7(self):
        wayfinder = wiener.FigureWayFinder([{"direction": -1, "length": 1}], 2000, 0.5, 30, {})
        self.assertEqual(wayfinder.node_direction_check(B, A, F, 2), False)

    def test_8(self):
        wayfinder = wiener.FigureWayFinder([{"direction": -1, "length": 1}], 2000, 0.5, 90, {})
        self.assertEqual(wayfinder.node_direction_check(B, A, G, 2), True)




unittest.main()
