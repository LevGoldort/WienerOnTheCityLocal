import math
import os
import sys
import unittest

# sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
# # https://stackoverflow.com/questions/16780014/import-file-from-parent-directory

import figureway.wiener as wiener

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


A = {'y': 320587653, 'x': 347698838}  # KISHON / MATALON
B = {'y': 320588007, 'x': 347702842}  # MATALON / GILADI
C = {'y': 320580717, 'x': 347704126}  # WOLFSON / GILADI (to the right from AB, 90deg)
D = {'y': 320580247, 'x': 347699899}  # WOLFSOM / KISHON (to the right from AB, 110deg)
E = {'y': 320581673, 'x': 347715051}  # WOLFSON / HASHUK (to the right but far away)
F = {'y': 320587125, 'x': 347694584}  # MIZRAHI / MATALON (on AB, FAB)
G = {'y': 320588484, 'x': 347707568}  # HERZL / MATALON (on AB, ABG)
H = {'y': 320596695, 'x': 347701645}  # GILADI / LEVINSKI (To the left from AB)


class TestNodeDirectionCheck(unittest.TestCase):

    def test_1(self):
        wayfinder = wiener.FigureWayFinder([{"direction": -1, "length": 1}], 2000, 0.5, 30, {})
        self.assertEqual(wayfinder.node_direction_check(A, B, C, 1), False)

    def test_2(self):
        wayfinder = wiener.FigureWayFinder([{"direction": 1, "length": 1}], 2000, 0.5, 40, {})
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

    def test_9(self):
        wayfinder = wiener.FigureWayFinder([{"direction": -1, "length": 1}], 2000, 0.5, 90, {})
        self.assertEqual(wayfinder.node_direction_check(B, A, H, -1), True)


# class RotateCheck(unittest.TestCase):
#
#     def test_1(self):
#         self.assertEqual(wiener.rotate(0, 0, 1, 0, math.pi/2), (0, 1))
#
#     def test_2(self):
#         self.assertEqual(wiener.rotate(0, 0, 1, 0, -math.pi/2), (0, -1))
#
#     def test_3(self):
#         self.assertEqual(wiener.rotate(0, 0, 1, 0, math.pi), (-1, 0))
#
#     def test_4(self):
#         self.assertEqual(wiener.rotate(0, 0, -1, 0, math.pi/2), (0, -1))
#
#     def test_5(self):
#         self.assertEqual(wiener.rotate(0, 0, 0, -1, math.pi/2), (1, 0))


if __name__ == '__main__':
    unittest.main()
