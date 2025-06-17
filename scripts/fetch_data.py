import requests
from bs4 import BeautifulSoup
import json
import time

HEADERS = {
    "User-Agent": "Mozilla/5.0 (compatible; GitHubActionsBot/1.0)"
}

def fetch_persons_from_category(category_url, limit=None):
    persons = []
    try:
        resp = requests.get(category_url, headers=HEADERS)
        resp.raise_for_status()
        soup = BeautifulSoup(resp.text, "html.parser")
        links = soup.select("div.mw-category-group ul li a")
        if limit:
            links = links[:limit]
        for a in links:
            name = a.get_text(strip=True)
            link = "https://zh.wikipedia.org" + a["href"]

            desc = ""
            img = ""
            birth = ""
            death = ""

            try:
                p_resp = requests.get(link, headers=HEADERS)
                p_resp.raise_for_status()
                p_soup = BeautifulSoup(p_resp.text, "html.parser")

                for p in p_soup.select("div.mw-parser-output > p"):
                    text = p.get_text(strip=True)
                    if text:
                        desc = text
                        break

                infobox_img = p_soup.select_one("table.infobox img")
                if infobox_img and infobox_img.has_attr("src"):
                    img = "https:" + infobox_img["src"]

                b_elem = p_soup.select_one("span.bday")
                if b_elem:
                    birth = b_elem.get_text(strip=True)

                d_elem = p_soup.select_one("span.dday")
                if d_elem:
                    death = d_elem.get_text(strip=True)
            except Exception:
                pass

            persons.append({
                "name": name,
                "birth": birth,
                "death": death,
                "description": desc,
                "link": link,
                "img": img
            })
            time.sleep(1)
    except Exception:
        pass
    return persons

def fetch_today_news(limit=10):
    url = "https://zh.wikipedia.org/wiki/Wikipedia:今日条目"
    news = []
    try:
        resp = requests.get(url, headers=HEADERS)
        resp.raise_for_status()
        soup = BeautifulSoup(resp.text, "html.parser")

        lis = soup.select("#mf-tfp > ul > li")[:limit]
        for li in lis:
            a = li.find("a")
            if not a:
                continue
            title = a.get_text(strip=True)
            link = "https://zh.wikipedia.org" + a["href"]
            desc = li.get_text(strip=True).replace(title, "").strip()

            img = ""
            try:
                entry_resp = requests.get(link, headers=HEADERS)
                entry_resp.raise_for_status()
                entry_soup = BeautifulSoup(entry_resp.text, "html.parser")
                img_tag = entry_soup.select_one("table.infobox img")
                if img_tag and img_tag.has_attr("src"):
                    img = "https:" + img_tag["src"]
            except Exception:
                pass

            news.append({
                "title": title,
                "link": link,
                "description": desc,
                "img": img
            })
            time.sleep(1)
    except Exception:
        pass
    return news

def main():
    print("爬取近代历史人物（80个）...")
    modern = fetch_persons_from_category("https://zh.wikipedia.org/wiki/Category:近代名人", limit=80)

    print("爬取公元后名人（非近代，10个）...")
    post_ancient = fetch_persons_from_category("https://zh.wikipedia.org/wiki/Category:公元后名人", limit=10)

    print("爬取公元前名人（10个）...")
    pre_ancient = fetch_persons_from_category("https://zh.wikipedia.org/wiki/Category:公元前名人", limit=10)

    historical_data = {
        "modern": modern,
        "postAncient": post_ancient,
        "preAncient": pre_ancient
    }

    with open("data/historical_persons.json", "w", encoding="utf-8") as f:
        json.dump(historical_data, f, ensure_ascii=False, indent=2)

    print("爬取今日条目新闻...")
    news = fetch_today_news(limit=10)
    with open("data/news.json", "w", encoding="utf-8") as f:
        json.dump(news, f, ensure_ascii=False, indent=2)

    print("数据保存完成。")

if __name__ == "__main__":
    main()
