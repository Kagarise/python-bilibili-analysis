import re

import requests
from bs4 import BeautifulSoup

from utils.logger import logger
from utils.mysql import fetch, commit
from utils.proxy import get_proxy, delete_proxy


class config:
    re_bv_url = re.compile(r'href="//(.*?)\?from=search"')
    re_digit = re.compile(r'\d+')
    re_coin = re.compile(r'</i>(.*?)</span>', re.S)
    re_tag1 = re.compile(r'<span>(.*?)</span>', re.S)
    re_tag2 = re.compile(r'<span class="channel-name">(.*?)</span>', re.S)
    re_tag3 = re.compile(r'target="_blank">(.*?)</a>', re.S)
    headers = {
        'user-agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/89.0.4389.90 Safari/537.36'
    }
    search_url = 'https://search.bilibili.com/all?keyword='
    page_url_param = '&page='
    order_url_param = '&order='
    video_url = 'https://www.bilibili.com/video/'
    order = {'最多点击': 'click', '最新发布': 'pubdate', '最多弹幕': 'dm', '最多收藏': 'stow'}


class sql_config:
    TABLE_EXIST = 0
    CREATE_SUCCESS = 1
    CREATE_FAIL = -1


class bilibili:
    def __init__(self, key):
        self.key = key
        self.headers = config.headers
        self.search_url = config.search_url + key
        self.page_url_param = config.page_url_param
        self.order_url_param = config.order_url_param
        self.pages = 0
        self.video_list = []
        self.data_list = []

    def search(self):
        try:
            if self.create_database() == sql_config.CREATE_SUCCESS:
                pages = self.get_key_pages()
                logger.success(f'查询 "{self.key}" 共有 {pages} 页')
                for page in range(1, pages + 1):
                    logger.success(f'正在查询 "{self.key}" ：第 {page} 页')
                    self.get_bv(page)
                    self.get_data()
                    logger.success(f'"{self.key}" 第{page}页数据查询完成')
                logger.success(f'获取 "{self.key}" 所有稿件信息成功')
                if self.commit_data():
                    logger.success(f'搜索关键字 "{self.key}" 并上传到数据库成功')
                else:
                    logger.error(f'上传 "{self.key}" 数据时失败')
        except:
            logger.error(f'搜索 "{self.key}" 失败')

    # 使用代理得到html页面
    def get_html(self, url):
        try:
            proxy = get_proxy()['proxy']
            proxies = {
                'http': 'http://' + proxy
            }
            logger.info(f'使用代理：{proxy}')
            retry_count = 5
            while retry_count > 0:
                try:
                    response = requests.get(url=url, headers=self.headers, proxies=proxies)
                    response.encoding = "utf-8"
                    return response.text
                except:
                    retry_count = -1
            delete_proxy(proxy)
            logger.info(f'删除代理：{proxy}')
            return ''
        except:
            logger.warning('无可用代理')
            return ''

    # 获取页数
    def get_key_pages(self):
        url = self.search_url
        html = self.get_html(url)
        soup = BeautifulSoup(html, "html.parser")
        try:
            pages = int(soup.select('.last > .pagination-btn')[0].text.strip())
            self.pages = pages
            return pages
        except:
            logger.error('获取页数失败')
            return 0

    # 获取所有video链接
    def get_bv(self, page, order='最多点击'):
        # 遍历每一页
        video_list = []
        try:
            url = f'{self.search_url}{self.page_url_param}{page}{self.order_url_param}{config.order[order]}'
            html = self.get_html(url)
            soup = BeautifulSoup(html, "html.parser")
            # print(soup.prettify())
            # 遍历这一页的每一个video
            videos = soup.select('.img-anchor')
            for video in videos:
                url_bv = f'https://{re.findall(config.re_bv_url, str(video))[0]}'
                video_list.append(url_bv)
            self.video_list = video_list
        except:
            logger.error('获取video链接失败')

    # 获取单个稿件所需信息
    def get_data(self):
        for url in self.video_list:
            # 不注释只获取一条信息
            # if url != self.video_list[0]:
            #     break
            html = self.get_html(url)
            soup = BeautifulSoup(html, "html.parser")
            data = dict()
            # 链接
            data['url'] = url
            # 标题
            title = soup.select('.video-title')[0]['title']
            data['title'] = title
            # 发布日期
            date = soup.select('.video-data > span')[2].string[:10]
            data['date'] = date
            # 发布时间
            time = soup.select('.video-data > span')[2].string[11:]
            data['time'] = time
            # 播放
            view = soup.select('.video-data > .view')[0]['title']
            view = re.findall(config.re_digit, str(view))[0]
            data['view'] = int(view)
            # 弹幕
            danmu = soup.select('.video-data > .dm')[0]['title']
            danmu = re.findall(config.re_digit, str(danmu))[0]
            data['danmu'] = int(danmu)
            # 点赞
            like = soup.select('.ops > .like')[0]['title'].strip()
            like = re.findall(config.re_digit, str(like))[0]
            data['like'] = int(like)
            # 投币
            coin = soup.select('.ops > .coin')[0]['title'].strip()
            valid_coin = config.re_digit.search(str(coin))
            # 不能获取精确投币量（未登录或登录已投币）
            if valid_coin is None:
                coin = soup.select('.ops > .coin')[0].text
                # 投币数量为0时，coin值为"投币"
                if coin.find('投币') != -1:
                    coin = 0
                else:
                    coin = int(float(coin.replace('万', '')) * 10000)
            else:
                coin = re.findall(config.re_digit, str(coin))[0]
            data['coin'] = int(coin)
            # 收藏
            collect = soup.select('.ops > .collect')[0]['title'].strip()
            # 收藏数量为0时，collect值为"收藏人数"
            if collect == "收藏人数":
                collect = 0
            else:
                collect = re.findall(config.re_digit, str(collect))[0]
            data['collect'] = int(collect)
            # 分享
            share = soup.select('.ops > .share')[0].text.strip()
            # 分享数量为0时，share值为"分享"
            if share == '分享':
                share = 0
            data['share'] = int(share)
            # 评论（获取不到？）
            # discuss = soup.select('.b-head .results')[0].text
            # data['discuss'] = discuss
            # 简介
            info = soup.select('.info')[0].text.strip()
            # 评论长度超过233将被截取
            data['info'] = info[:233]
            # Tag
            tags = soup.select('.tag')
            tags1 = re.findall(config.re_tag1, str(tags))
            tags2 = re.findall(config.re_tag2, str(tags))
            tags3 = [tag.strip() for tag in re.findall(config.re_tag3, str(tags))[len(tags1) + len(tags2):]]
            tags = '/'.join(set(tags1 + tags2 + tags3))
            data['tags'] = tags
            # 将稿件数据添加到data_list
            self.data_list.append(data)

    # 创建数据库
    def create_database(self):
        try:
            table_name = self.key.replace(' ', '')
            # 若每次都重新查找，可加DROP
            # sql = f'DROP TABLE IF EXISTS {table_name};'
            # commit(sql)
            # WARNING: 存在sql注入问题，但并未返回实质性信息
            sql = f'SELECT TABLE_NAME FROM information_schema.TABLES WHERE TABLE_SCHEMA = "bilibili" AND TABLE_NAME = "{table_name}"'
            result = fetch(sql)
            exist = bool(result)
            if exist is False:
                logger.info('创建数据库成功')
                sql = f'''CREATE TABLE {table_name} (
id INT NOT NULL AUTO_INCREMENT PRIMARY KEY COMMENT 'ID',
url VARCHAR(255) NOT NULL COMMENT '链接',
title VARCHAR(255) NOT NULL COMMENT '标题',
date VARCHAR(255) NOT NULL COMMENT '发布日期',
time VARCHAR(255) NOT NULL COMMENT '发布时间',
view INT NOT NULL COMMENT '播放',
danmu INT NOT NULL COMMENT '弹幕',
love INT NOT NULL COMMENT '点赞',
coin INT NOT NULL COMMENT '投币',
collect INT NOT NULL COMMENT '收藏',
share INT NOT NULL COMMENT '分享',
info VARCHAR(255) NOT NULL COMMENT '简介',
tags VARCHAR(255) NOT NULL COMMENT '标签',
create_time TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
update_time TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT '更新时间'
)ENGINE=InnoDB AUTO_INCREMENT=1 DEFAULT CHARSET=utf8mb4;
'''
                commit(sql)
                return sql_config.CREATE_SUCCESS
            else:
                logger.success('数据库已存在，无需创建')
                return sql_config.TABLE_EXIST
        except:
            logger.error('创建数据库失败')
            return sql_config.CREATE_FAIL

    # 将获取到的信息添加到数据库
    def commit_data(self):
        try:
            table_name = self.key.replace(' ', '')
            sql = f'INSERT INTO {table_name} (url, title, date, time, view, danmu, love, coin, collect, share, info, tags) VALUES \n'
            for v in self.data_list:
                sql += f"('{v['url']}','{v['title']}','{v['date']}','{v['time']}','{v['view']}','{v['danmu']}','{v['like']}','{v['coin']}','{v['collect']}','{v['share']}','{v['info']}','{v['tags']}'),\n"
            sql = sql[:-2] + ';'
            logger.debug(sql)
            commit(sql)
            logger.info(f'{self.key} 数据添加成功')
            return True
        except:
            logger.error('数据库添加数据出错')
            return False
