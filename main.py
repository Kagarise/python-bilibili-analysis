from models.bilibili import bilibili

if __name__ == "__main__":
    search_key = '小团子酱 杨雪'
    B = bilibili(search_key)
    B.search()
