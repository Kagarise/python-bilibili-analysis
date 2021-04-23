from flask import Flask
from flask_cors import CORS

from routes import init_routes

SERVER_INFO = {
    'port': 520,
    'host': '0.0.0.0',
    'debug': False,
}

if __name__ == "__main__":
    # 获取数据
    # from models.bilibili import bilibili
    # search_key = '小团子酱 杨雪'
    # B = bilibili(search_key)
    # B.search()
    app = Flask(__name__)
    CORS(app, supports_credentials=True)
    init_routes(app)
    app.run(**SERVER_INFO)
