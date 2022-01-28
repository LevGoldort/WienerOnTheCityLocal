import logging
import figureway.wiener as wiener
import figureway.staticmethods as static
import os
import configparser
import boto3
import botocore
import pickle

if __name__ == '__main__':
    cfg = configparser.ConfigParser()
    cfg.read(os.path.join(os.path.dirname(__file__), 'config.cfg'))
    city_list_path = cfg.get('INPUT_PATH', 'city_list', fallback='Wrong Config file')

    amazon_access_key_id = cfg.get('DEFAULT', 'aws_access_key_id')
    amazon_secret_key = cfg.get('DEFAULT', 'aws_secret_access_key')
    amazon_bucket_name = cfg.get('DEFAULT', 'aws_s3_bucket')
    city_list = static.load_city_list(city_list_path)
    closest_city = static.find_closest_city(32.054658400260834, 34.75611337395264, city_list)
    print(closest_city)

    city_filepath = '/Static/' + closest_city['country'] + '/' + closest_city['lat'] + closest_city['lng'] + '.pickle'

    session = boto3.Session(aws_access_key_id=amazon_access_key_id, aws_secret_access_key=amazon_secret_key)
    s3 = session.resource('s3')
    obj = s3.Object(amazon_bucket_name, city_filepath)
    obj.load()
    crossroads_pickle = obj.get()['Body'].read()
    crossroads = pickle.loads(crossroads_pickle)
    cl = wiener.FigureWayFinder(wiener.penis_dict, 2000, 0.75, 45, crossroads)

    cl.find_figure_way(32.054658400260834, 34.75611337395264)
    print(len(cl.ways_found))
    for element in cl.ways_found:
        print(element['ratio'])
        print(element['way'])
        print(wiener.show_way_by_points(element['way'], cl.graph))

    print('da best route is', cl.get_best_route())
    ways = cl.continue_straight(357535535, 7920335245)

