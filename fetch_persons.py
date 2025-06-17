import requests
from bs4 import BeautifulSoup
import json
import time

BASE_URL = 'https://zh.wikipedia.org'

def fetch_persons(category_url, max_count=100):
    headers = {'User-Agent': 'Mozilla/5.0'}
    persons = []
    url = category_url
    visited = set()
    while url and len(persons) < max_count:
        resp = requests.get(url, headers=headers)
        soup = BeautifulSoup(resp.text, 'html.parser')
        
        for li in soup.select('div.mw-category-group ul li'):
            if len(persons) >= max_count:
                break
            a = li.find('a')
            if not a or a['href'] in visited:
                continue
            visited.add(a['href'])

            name = a.text
            link = BASE_URL + a['href']
            
            desc = ''
            img_url = ''
            try:
                person_resp = requests.get(link, headers=headers)
                person_soup = BeautifulSoup(person_resp.text, 'html.parser')

                # 简介抓首段
                p = person_soup.select_one('div.mw-parser-output > p:not(.mw-empty-elt)')
                if p:
                    desc = p.get_text(strip=True)

                # 图片抓infobox首图
                img = person_soup.select_one('table.infobox img')
                if img and img.has_attr('src'):
                    img_url = 'https:' + img['src']
            except Exception:
                pass

            persons.append({
                'name': name,
                'link': link,
                'description': desc,
                'img': img_url,
            })
            time.sleep(0.5)
            
        # 下一页链接（翻页）
        next_link = soup.select_one('a[title^="Category:"][title$="(分页)"]')
        if next_link and next_link.has_attr('href'):
            url = BASE_URL + next_link['href']
        else:
            url = None
    return persons

if __name__ == '__main__':
    # 近代历史人物，目标80个（多取点保证够）
    modern_url = 'https://zh.wikipedia.org/wiki/Category:近代人物'
    modern_persons = fetch_persons(modern_url, 80)

    # 公元后古代人物，目标10个
    post_ancient_url = 'https://zh.wikipedia.org/wiki/Category:公元后历史人物'
    post_ancient_persons = fetch_persons(post_ancient_url, 10)

    # 公元前历史人物，目标10个
    pre_ancient_url = 'https://zh.wikipedia.org/wiki/Category:公元前历史人物'
    pre_ancient_persons = fetch_persons(pre_ancient_url, 10)

    data = {
        'modern': modern_persons,
        'postAncient': post_ancient_persons,
        'preAncient': pre_ancient_persons
    }

    with open('data/historical_persons.json', 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=2)
