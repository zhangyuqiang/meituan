import json
from get_proxy import get_random_proxy
import requests
from bs4 import BeautifulSoup
from workers import app
import requests
from scrapy import Selector
import time

_ = int(time.time() * 1000)
url = "http://i.waimai.meituan.com/openh5/poi/food?_={}".format(_)

headers = {
    "User-Agent": "Mozilla/5.0 (Linux; Android 5.0; SM-G900P Build/LRX21T) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/70.0.3538.102 Mobile Safari/537.36",
    "Referer": "http://i.waimai.meituan.com/openh5/homepage/poilist",
    "Host": "i.waimai.meituan.com",
    "Origin": "http://h5.waimai.meituan.com",
    "Accept": "application/json",
    "Accept-Encoding": "gzip, deflate",
    "Accept-Language": "zh-CN,zh;q=0.9,en;q=0.8",
    "Connection": "keep-alive",
    "Content-Length": "180",
    "Content-Type": "application/x-www-form-urlencoded",

}


@app.task
def crawl(shop):
    print('正在抓取链接{}'.format(shop))
    content = parse_detail(shop)
    # print(content)
    item = {}
    # products =[]
    if content.get("code") == 1:
        item["products"] = None
    else:
        item["shop_name"] = content.get("data").get("shopInfo").get("shopName")
        item["shop_id"] = shop.get("shop_id")
        item["promptText"] = content.get("data").get("shoppingCart").get("promptText")
        item["shipping_time"] = content.get("data").get("shopInfo").get("shipping_time")
        item["deliveryTime"] = content.get("data").get("shopInfo").get("deliveryTime")
        products_list = content.get("data").get("categoryList")
        item["products"] = []
        for product in products_list:
            spulist = product.get("spuList")
            if product.get("categoryName") != "店家食材展示勿点":
                for spu in spulist:
                    i = {}
                    i["shop_id"] = shop.get("shop_id")
                    i["spu_name"] = spu.get("spuName")
                    i["current_price"] = spu.get("currentPrice")  # 现价
                    i["origin_price"] = spu.get("originPrice")  # 原价
                    i["img"] = spu.get("littleImageUrl")  # 原价
                    if i["img"]:
                        if i not in item["products"]:
                            item["products"].append(i)
    # print(item)
    content = parse_address(shop)
    # print(content)
    item["address"] = content.get("data").get("shopAddress")
    item["phone"] = content.get("data").get("shopPhone")
    # print(address, phone)
    content = parse_evaluate(shop)
    # print(content)
    if content.get("code") != 1:
        data = content.get("data")
        if data:
            item["praise_ratio"] = data.get("PraiseRatio")
            item["evaluate"] = []
            evaluates = data.get("list")
            if evaluates:
                for evaluate in evaluates:
                    if evaluate.get("content") not in item["evaluate"]:
                        # print(evaluate)
                        item["evaluate"].append(evaluate.get("content"))

            total = data.get("recordCount")
            nextindex = data.get("nextStartIndex")
            for i in range((int(total)//20)):
                # print("下一页")
                content = parse_evaluate(shop,nextindex)
                nextindex = content.get("data").get("nextStartIndex")

                data = content.get("data")
                # print(data)
                if data:
                    evaluates = data.get("list")
                    if evaluates:
                        for evaluate in evaluates:
                            # print(evaluate)
                            cont = evaluate.get("content")
                            if cont:
                                item["evaluate"].append(cont)
                # print(content)

    # print(item)
    # print(item["evaluate"])
    # print(len(item["evaluate"]))
    return item


def rpost(url, data):
    while True:
        try:
            # print(data,)
            # print(headers)
            # print(get_random_proxy)
            resp = requests.post(url, data=data, headers=headers, proxies=get_random_proxy(), timeout=20)
            if resp.status_code == 200:
                return resp

        except Exception as e:
            print(e)
            # time.sleep(10)
            pass


def parse_detail(shop):
    data = {
        "geoType": "2",
        "mtWmPoiId": shop.get("shop_id"),
        "dpShopId": "-1",
        "source": "shoplist",
        # "sortId": "0",
        "wm_latitude": "{}".format(int(shop.get("x") * 10 ** 6)),  # 39912289
        "wm_longitude": "{}".format(int(shop.get("y") * 10 ** 6)),  # 116365868
    }
    # print(data)
    headers[
        "Cookie"] = 'uuid=0c930c6315394f57bcd4.1546058773.1.0.0; _lxsdk_cuid=167f848b869c8-07cfbb16ea70cf-3f674604-1fa400-167f848b86ac8; _ga=GA1.3.106177890.1546058776; _gid=GA1.3.1457812280.1546058776; _lx_utm=utm_source%3DBaidu%26utm_medium%3Dorganic; __mta=247233467.1546058778366.1546058778366.1546058778366.1; terminal=i; w_utmz="utm_campaign=(direct)&utm_source=5000&utm_medium=(none)&utm_content=(none)&utm_term=(none)"; w_uuid=X0Qg7ezlPGsZCkz8wRXWyt5fvFJDaP0trQXGs7rkTM1l6Bbb5CccGSxmiDUOPLyb; utm_source=0; wx_channel_id=0; JSESSIONID=1h9ctnob8to9ugis02tzmakgv; webp=1; __mta=247233467.1546058778366.1546058778366.1546058783530.2; w_addr=; w_actual_lat={}; w_actual_lng={}; wm_order_channel=default; openh5_uuid=; openh5_uuid=IOx-ogmFpg3ct-USwbINQsaW87IP2zpvKruvBp9JVT57WZLe5-QsANvjDdObob4b; w_visitid=780c0fd7-5672-44d7-bb69-b20fdd0cd2a9; _lxsdk_s=%7C%7C3'.format(
        data["wm_latitude"], data["wm_longitude"])
    resp = rpost(url, data=data)
    content = json.loads(resp.content.decode())
    return content


def parse_address(shop):
    phone_url = "http://i.waimai.meituan.com/openh5/poi/info?_={}".format(_)
    x = shop.get("x")
    y = shop.get("y")
    form_data = {
        "shopId": "0",
        "mtWmPoiId": shop.get("shop_id"),
        "source": "searchresult",
        "channel": "6",
        "lng": x,
        "lat": y,
        "gpsLng": x,
        "gpsLat": y,
        "wm_latitude": "0",
        "wm_longitude": "0",
        "wm_actual_latitude": int(x * 10 ** 6),
        "wm_actual_longitude": int(y * 10 ** 6),
    }
    resp = rpost(phone_url, data=form_data)
    data = json.loads(resp.content.decode())
    return data


def parse_evaluate(shop,index=0):
    # time.sleep(5)
    url = "http://i.waimai.meituan.com/openh5/poi/comments?_={}".format(_)
    x = shop.get("x")
    y = shop.get("y")
    form_data = {
        "lng": x,
        "lat": y,
        "gpsLng": x,
        "gpsLat": y,
        "shopId": "0",
        "mtWmPoiId": shop.get("shop_id"),
        "startIndex": str(index),
        "labelId": "0",
        "scoreType": "0",
        "wm_actual_latitude": int(x * 10 ** 6),
        "wm_actual_longitude": int(y * 10 ** 6),
    }
    resp = rpost(url, data=form_data)
    content = json.loads(resp.content.decode())
    return content


if __name__ == '__main__':
    data = {
        "x": 31.247277,
        "shop_id": "464806670412837",
        "y": 122.01801
    }
    crawl(data)
