import requests
from bs4 import BeautifulSoup
import json
import os

DATA_DIR = 'data'
HISTORICAL_FILE = os.path.join(DATA_DIR, 'historical_persons.json')
NEWS_FILE = os.path.join(DATA_DIR, 'news.json')

def fetch_historical_persons():
    # 这里用维基百科“历史人物列表(近代)”等页面示范爬取，真实爬取请按需求拓展

    base_url = "https://zh.wikipedia.org"
    categories = {
        "modern": "https://zh.wikipedia.org/wiki/Category:%E8%BF%91%E4%BB%A3%E5%8E%86%E5%8F%B2%E4%BA%BA%E7%89%A9",
        "postAncient": "https://zh.wikipedia.org/wiki/Category:%E5%85%AC%E5%85%83%E5%90%8E%E5%8E%86%E5%8F%B2%E4%BA%BA%E7%89%A9",
        "preAncient": "https://zh.wikipedia.org/wiki/Category:%E5%85%AC%E5%85%83%E5%89%8D%E5%8E%86%E5%8F%B2%E4%BA%BA%E7%89%A9"
    }

    result = {"modern": [], "postAncient": [], "preAncient": []}

    for key, url in categories.items():
        print(f"爬取类别 {key} ...")
        resp = requests.get(url)
        if resp.status_code != 200:
            print(f"无法访问 {url}")
            continue
        soup = BeautifulSoup(resp.text, 'html.parser')
        # 维基分类页面中人物链接通常在 div#mw-pages 中的 ul > li > a
        div_pages = soup.find('div', id='mw-pages')
        if not div_pages:
            print(f"{url} 页面结构异常")
            continue
        links = div_pages.find_all('a')
        count = 0
        for a in links:
            if count >= (80 if key=="modern" else 10):
                break
            href = a.get('href')
            name = a.get_text(strip=True)
            if not href or not name:
                continue
            full_url = base_url + href
            # 访问人物页面抓取简介和图片
            desc, img = fetch_person_detail(full_url)
            person = {
                "name": name,
                "birth": "",
                "death": "",
                "img": img or "",
                "description": desc or "无简介",
                "link": full_url
            }
            result[key].append(person)
            count += 1
        print(f"{key} 共抓取 {count} 个")

    return result

def fetch_person_detail(url):
    try:
        resp = requests.get(url)
        if resp.status_code != 200:
            return "", ""
        soup = BeautifulSoup(resp.text, 'html.parser')
        # 抓取页面第一个段落作为简介
        p = soup.select_one('div.mw-parser-output > p')
        desc = p.get_text(strip=True) if p else ""

        # 抓取第一张主要图片
        img_tag = soup.select_one('table.infobox img')
        img_url = ""
        if img_tag and img_tag.has_attr('src'):
            src = img_tag['src']
            if src.startswith("//"):
                img_url = "https:" + src
            elif src.startswith("http"):
                img_url = src
            else:
                img_url = "https://zh.wikipedia.org" + src
        return desc, img_url
    except Exception as e:
        print(f"抓取 {url} 详情异常：{e}")
        return "", ""

def fetch_news():
    # 简单示范：抓取人民网首页新闻标题和图片（可自行换成其他可靠新闻源）
    url = "http://news.people.com.cn/"
    try:
        resp = requests.get(url)
        if resp.status_code != 200:
            return []
        soup = BeautifulSoup(resp.text, 'html.parser')
        news_items = []
        # 这里抓取示例，仅抓取前5条
        for item in soup.select('.hdnewslist li a')[:5]:
            title = item.get_text(strip=True)
            link = item.get('href')
            if not link.startswith('http'):
                link = "http://news.people.com.cn" + link
            # 没有图则用占位图
            img_url = "https://via.placeholder.com/120x120?text=新闻"
            news_items.append({
                "title": title,
                "desc": title,
                "img": img_url,
                "link": link
            })
        return news_items
    except Exception as e:
        print(f"抓取新闻异常：{e}")
        return []

def main():
    os.makedirs(DATA_DIR, exist_ok=True)

    print("开始抓取历史人物数据...")
    persons = fetch_historical_persons()
    with open(HISTORICAL_FILE, 'w', encoding='utf-8') as f:
        json.dump(persons, f, ensure_ascii=False, indent=2)
    print(f"已保存到 {HISTORICAL_FILE}")

    print("开始抓取时事新闻...")
    news = fetch_news()
    with open(NEWS_FILE, 'w', encoding='utf-8') as f:
        json.dump(news, f, ensure_ascii=False, indent=2)
    print(f"已保存到 {NEWS_FILE}")

if __name__ == "__main__":
    main()
