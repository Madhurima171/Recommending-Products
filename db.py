import pymysql


def get_connection():
    return pymysql.connect(
        host='localhost',
        user='root',
        password='',
        database='product_recommender',
        cursorclass=pymysql.cursors.DictCursor
    )