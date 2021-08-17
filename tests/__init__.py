import wiener

# All Israel file, 83 mb:
israel_osm = "/Users/levgoldort/Downloads/israel-and-palestine-latest.osm.pbf"
# Holon near my house, 2km2:
near_house_osm = "/Users/levgoldort/Downloads/planet_34.762,32.004_34.781,32.015.osm.pbf"
california_osm = "/Users/levgoldort/Downloads/planet_-120.0394,38.8848_-119.9224,38.9521.osm.pbf"
moscow_osm = "/Users/levgoldort/Downloads/planet_37.297,55.608_37.96,55.893.osm.pbf"

w = wiener.GenerateGraphHandler(32.05484684105788, 34.769174207787024, 5000)
w.apply_file(israel_osm, locations=True)

cl = wiener.FigureWayFinder(penis, 3000, 0.4, 90, crossroads)
cl.find_figure_way(32.05484684105788, 34.769174207787024)


def test_simple_turn():
    graph = {
        1: {x: 10, y: 20},
        2: {x: 20, y: 20},
        3: {x: 20, y: 40},
        4: {x: 20, y: 40},
        5: {x: 20, y: 40},
    }
    figure = [1]
    result = find_figure_way(...)
    self.assertEquals(result, [1, 2, 3])


def test_sqrt():
    a = 2
    b = 4
    self.assertEquals(sqrt(4), a)
    if sqrt(4) == a:
        print("Success")
    else:
        print("Failure")