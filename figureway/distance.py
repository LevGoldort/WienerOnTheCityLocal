import math

def distance(lat0, lon0, lat1, lon1):
    # Return distance in meters between two dots
    # https://stackoverflow.com/questions/639695/how-to-convert-latitude-or-longitude-to-meters
    earth_radius = 6378.137
    d_lat = lat1 * math.pi / 180 - lat0 * math.pi / 180
    d_lon = lon1 * math.pi / 180 - lon0 * math.pi / 180
    a = math.sin(d_lat / 2) ** 2 + math.cos(lat0 * math.pi / 180) * math.cos(lat1 * math.pi / 180) \
        * math.sin(d_lon / 2) ** 2
    c = 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))

    return earth_radius * c * 1000