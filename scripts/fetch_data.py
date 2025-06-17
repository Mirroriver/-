import requests
from bs4 import BeautifulSoup
import json
import os
from datetime import datetime

DATA_DIR = 'data'
HISTORICAL_FILE = os.path.join(DATA_DIR, 'historical_persons.json')
NEWS_FILE = os.path.join(DATA_DIR, 'news.json')

def fetch_historical_persons():
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
        div_pages = soup.find('div', id='mw-pages')
        if not div_pages:
            print(f"{url} 页面结构异常")
            continue
        links = div_pages.find_all('a')
        count = 0
        limit = 80 if key=="modern" else 10
        for a in links:
            if count >= limit:
                break
            href = a.get('href')
            name = a.get_text(strip=True)
            if not href or not name:
                continue
            full_url = base_url + href
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
        p = soup.select_one('div.mw-parser-output > p')
        desc = p.get_text(strip=True) if p else ""

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

def fetch_wiki_today_events():
    # 维基百科“当天日期”页面，例如 https://zh.wikipedia.org/wiki/2025%E5%B9%B46%E6%9C%8817%E6%97%A5
    today = datetime.utcnow()  # UTC时间
    # 转成中文日期格式：YYYY年M月D日
    date_str = f"{today.year}年{today.month}月{today.day}日"
    url = f"https://zh.wikipedia.org/wiki/{date_str}"
    print(f"爬取今日事件页面: {url}")
    try:
        resp = requests.get(url)
        if resp.status_code != 200:
            print(f"访问失败: {resp.status_code}")
            return []
        soup = BeautifulSoup(resp.text, 'html.parser')

        # 目标是“历史事件”板块（中文维基习惯）
        # 先定位带有“历史事件”或“事件”字样的h2或h3标题，获取对应的ul列表
        events = []
        for header in soup.find_all(['h2','h3']):
            span = header.find('span', class_='mw-headline')
            if span and ('历史事件' in span.text or '事件' in span.text):
                # 找下一个ul或ol作为事件列表
                next_node = header.find_next_sibling()
                while next_node and next_node.name not in ['ul', 'ol']:
                    next_node = next_node.find_next_sibling()
                if next_node and next_node.name in ['ul','ol']:
                    lis = next_node.find_all('li')
                    for li in lis[:10]:  # 只取前10条事件
                        text = li.get_text(strip=True)
                        link = ""
                        img = ""
                        a = li.find('a')
                        if a and a.has_attr('href'):
                            link = "https://zh.wikipedia.org" + a['href']
                            # 尝试获取事件第一个链接页面的缩略图
                            img, _ = fetch_person_detail(link)
                        events.append({
                            "title": text,
                            "desc": text,
                            "img": img,
                            "link": link
                        })
                    break
        return events
    except Exception as e:
        print(f"抓取今日事件异常：{e}")
        return []

def main():
    os.makedirs(DATA_DIR, exist_ok=True)

    print("开始抓取历史人物数据...")
    persons = fetch_historical_persons()
    with open(HISTORICAL_FILE, 'w', encoding='utf-8') as f:
        json.dump(persons, f, ensure_ascii=False, indent=2)
    print(f"已保存到 {HISTORICAL_FILE}")

    print("开始抓取维基今日事件...")
    news = fetch_wiki_today_events()
    with open(NEWS_FILE, 'w', encoding='utf-8') as f:
        json.dump(news, f, ensure_ascii=False, indent=2)
    print(f"已保存到 {NEWS_FILE}")

if __name__ == "__main__":
    main()

