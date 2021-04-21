from models.bilibili import bilibili
from utils.logger import logger

if __name__ == "__main__":
    search_key = '小团子酱 杨雪'
    B = bilibili(search_key)
    pages = B.get_key_pages()
    logger.info(f'查询 \"{search_key}\" 共有 {pages} 页')
    B.get_bv()
    logger.info(f'共有 {len(B.video_list)} 个稿件')
    B.get_data()
    for v in B.data_list:
        print(v)
