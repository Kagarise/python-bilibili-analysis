from flask import Blueprint

from utils.logger import logger
from utils.mysql import fetch
from utils.result import Result

api = Blueprint('api', __name__, url_prefix='')


@api.route("/dango", methods=['post'])
def dango():
    try:
        data = fetch('SELECT * FROM 小团子酱杨雪')
        logger.success('查询 "小团子酱 杨雪" 完成')
        return Result.success(data)
    except:
        logger.success('查询 "小团子酱 杨雪" 失败')
        return Result.error(400, '获取数据失败')
