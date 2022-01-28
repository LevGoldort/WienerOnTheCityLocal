import configparser
import os
from mysql.connector import connect, Error


def connect_db():

    cfg = configparser.ConfigParser()
    cfg.read(os.path.join(os.path.dirname(__file__), 'config.cfg'))

    host = cfg.get('DB', 'db_endpoint')
    user = cfg.get('DB', 'db_user')
    port = int(cfg.get('DB', 'db_port'))
    password = cfg.get('DB', 'db_password')
    database = cfg.get('DB', 'db_database')

    connection = connect(host=host,
                         user=user,
                         password=password,
                         database=database,
                         port=port
                         )

    return connection


def db_save(connection, ):

    sql_query = '''CREATE TABLE `route_rates` (
        `id` int(11) NOT NULL AUTO_INCREMENT,
        `country` CHAR(2),
        `city` CHAR(40),
        `edge` FLOAT NOT NULL,
        `angle_allowance` FLOAT NOT NULL,
        `distance_allowance` FLOAT NOT NULL,
        `node0_lat` FLOAT NOT NULL,
        `node0_lon` FLOAT NOT NULL,
        `node1_lat` FLOAT NOT NULL,
        `node1_lon` FLOAT NOT NULL,
        `node2_lat` FLOAT NOT NULL,
        `node2_lon` FLOAT NOT NULL,
        `node3_lat` FLOAT NOT NULL,
        `node3_lon` FLOAT NOT NULL,
        `node4_lat` FLOAT NOT NULL,
        `node4_lon` FLOAT NOT NULL,
        `node5_lat` FLOAT NOT NULL,
        `node5_lon` FLOAT NOT NULL,
        `node6_lat` FLOAT NOT NULL,
        `node6_lon` FLOAT NOT NULL,
        `node7_lat` FLOAT NOT NULL,
        `node7_lon` FLOAT NOT NULL,
        `node8_lat` FLOAT NOT NULL,
        `node8_lon` FLOAT NOT NULL,
        `node9_lat` FLOAT NOT NULL,
        `node9_lon` FLOAT NOT NULL,
        `RATE` INT,
        PRIMARY KEY (`id`)
    ) '''

    connection.cursor().execute(sql_query)
    connection.commit()
    connection.close()
