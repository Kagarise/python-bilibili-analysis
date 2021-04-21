import re

import requests
from bs4 import BeautifulSoup

from utils.logger import logger
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


class bilibili:
    def __init__(self, key):
        self.headers = config.headers
        self.search_url = config.search_url + key
        self.page_url_param = config.page_url_param
        self.order_url_param = config.order_url_param
        self.pages = 0
        self.video_list = []
        self.data_list = []

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
    def get_bv(self, order='最多点击'):
        # 遍历每一页
        video_list = []
        try:
            for page in range(1, self.pages + 1):
                if page != 1:
                    break
                logger.info(f'正在查询：第 {page} 页')
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

    def get_data(self):
        for url in self.video_list:
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
            data['view'] = view
            # 弹幕
            danmu = soup.select('.video-data > .dm')[0]['title']
            danmu = re.findall(config.re_digit, str(danmu))[0]
            data['danmu'] = danmu
            # 点赞
            like = soup.select('.ops > .like')[0]['title']
            like = re.findall(config.re_digit, str(like))[0]
            data['like'] = like
            # 投币
            coin = soup.select('.ops > .coin')[0]['title']
            valid_coin = config.re_digit.search(str(coin))
            # 不能获取精确投币量（未登录或登录已投币）
            if valid_coin is None:
                coin = soup.select('.ops > .coin')[0].text
                coin = int(float(coin.replace('万', '')) * 10000)
            else:
                coin = re.findall(config.re_digit, str(coin))[0]
            data['coin'] = coin
            # 收藏
            collect = soup.select('.ops > .collect')[0]['title']
            collect = re.findall(config.re_digit, str(collect))[0]
            data['collect'] = collect
            # 分享
            share = soup.select('.ops > .share')[0].text.strip()
            data['share'] = share
            # 评论（获取不到？）
            # discuss = soup.select('.b-head .results')[0].text
            # data['discuss'] = discuss
            # 简介
            info = soup.select('.info')[0].text.strip()
            data['info'] = info
            # Tag
            tags = soup.select('.tag')
            tags1 = re.findall(config.re_tag1, str(tags))
            tags2 = re.findall(config.re_tag2, str(tags))
            tags3 = [tag.strip() for tag in re.findall(config.re_tag3, str(tags))[len(tags1) + len(tags2):]]
            tags = '/'.join(set(tags1 + tags2 + tags3))
            data['tags'] = tags
            # 将稿件数据添加到data_list
            self.data_list.append(data)
