import json
import logging
import figureway.wiener as wiener
import figureway.staticmethods as static
import os
import configparser
import boto3
import botocore
import pickle
import requests
import time
import asyncio
from datetime import datetime

async def runfunc(fwf, lat, lon):
    print('func for lat {} lon {} run at {}'.format(lat, lon, time.time()))
    await asyncio.sleep(0.01)
    fwf.find_figure_way(lat, lon)
    print('at {} found {} ways for lat {} lon {}'.format(time.time(), len(fwf.ways_found), lat, lon))


async def start():
    print("The time is {}, we are starting".format(time.time()))
    task1 = loop.create_task(runfunc(cl, 32.054658400260834, 34.75611337395264))
    task2 = loop.create_task(runfunc(second_cl, 31.895779936396874, 34.811260770896396))
    await asyncio.wait([task1, task2])

if __name__ == '__main__':

    # cfg = configparser.ConfigParser()
    # cfg.read(os.path.join(os.path.dirname(__file__), 'config.cfg'))
    # city_list_path = cfg.get('INPUT_PATH', 'city_list', fallback='Wrong Config file')
    #
    # amazon_access_key_id = cfg.get('DEFAULT', 'aws_access_key_id')
    # amazon_secret_key = cfg.get('DEFAULT', 'aws_secret_access_key')
    # amazon_bucket_name = cfg.get('DEFAULT', 'aws_s3_bucket')
    # city_list = static.load_city_list(city_list_path)
    # closest_city = static.find_closest_city(32.054658400260834, 34.75611337395264, city_list)
    # second_city = static.find_closest_city(31.895779936396874, 34.811260770896396, city_list)
    # print(closest_city)
    # print(second_city)
    #
    # city_filepath = '/Static/' + closest_city['country'] + '/' + closest_city['lat'] + closest_city['lng'] + '.pickle'
    # second_city_filepath = '/Static/' + second_city['country'] + '/' + second_city['lat'] + second_city['lng'] + '.pickle'
    #
    # session = boto3.Session(aws_access_key_id=amazon_access_key_id, aws_secret_access_key=amazon_secret_key)
    # s3 = session.resource('s3')
    # obj = s3.Object(amazon_bucket_name, city_filepath)
    # obj.load()
    # crossroads_pickle = obj.get()['Body'].read()
    # crossroads = pickle.loads(crossroads_pickle)
    # second_obj = s3.Object(amazon_bucket_name, second_city_filepath)
    # second_obj.load()
    # second_crossroads_pickle = obj.get()['Body'].read()
    # second_crossroads = pickle.loads(second_crossroads_pickle)
    # cl = wiener.FigureWayFinder(wiener.penis_dict, 2000, 0.75, 45, crossroads)
    # second_cl = wiener.FigureWayFinder(wiener.penis_dict, 2000, 0.75, 45, second_crossroads)
    #
    # loop = asyncio.get_event_loop()
    # loop.run_until_complete(start())
    # loop.close()

    # print(len(cl.ways_found))
    # print(cl.get_best_route())
    # payload = {'city_lat': closest_city['lat'],
    #            'city_lon': closest_city['lng'],
    #            'country': closest_city['country'],
    #            'bucket': amazon_bucket_name}
    #
    # headers = {'content-type': 'application/json'}
    #
    # client = boto3.client('lambda')
    #
    # response = client.invoke(FunctionName='find_figure_way',
    #                          InvocationType='RequestResponse',
    #                          Payload=json.dumps(payload))
    # print(response)
    # print(response['Payload'].read())



