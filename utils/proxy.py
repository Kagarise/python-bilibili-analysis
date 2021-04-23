import requests


class config:
    api_base = ''
    api_get = api_base + '/get'
    api_get_all = api_base + '/get_all'
    api_get_status = api_base + '/get_status'
    api_delete = api_base + '/delete'


def help_proxy():
    return eval(requests.get(config.api_base).text)


def get_proxy():
    return eval(requests.get(config.api_get).text)


def get_all_proxy():
    return eval(requests.get(config.api_get_all).text)


def get_status_proxy():
    return eval(requests.get(config.api_get_status).text)


def delete_proxy(proxy):
    return eval(requests.get(f'{config.api_delete}?proxy={proxy}').text)
