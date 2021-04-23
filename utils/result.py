class Result(object):
    @staticmethod
    def success(data=None):
        return {
            'code': 200,
            'msg': 'success',
            'data': data
        }

    @staticmethod
    def error(code, msg):
        return {
            'code': code,
            'msg': msg
        }
