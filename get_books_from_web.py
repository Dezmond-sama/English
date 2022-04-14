from os.path import exists
import requests
from bs4 import BeautifulSoup as bs
from fake_useragent import UserAgent
import json
import re


def get_links(max_count = 0):
    ua = UserAgent()
    link = "https://www.rulit.me/books/en/1/date?format=txt"
    books = []
    tags = {}
    while True:
        data = requests.get(link, headers={'User-Agent': ua.random})
        data = bs(data.content, "lxml")
        items = data.find(attrs={"class": "col-lg-9"}).find_all(attrs={"class": "post-content"})
        try:
            for item in items:
                categories = [i.getText() for i in item.find_all(attrs={"class": "post-cat"})]
                for tag in categories:
                    tags[tag] = tags.get(tag, 0) + 1
                href = item.find("h4").find("a").get("href")
                title = re.sub(r"[\\\|\/\:\*\?\"\<\>]", "", item.find("h4").find("a").getText())
                books.append({"href": href, "title": title, "categories": categories})
        except:
            break

        paginator = data.find("ul",attrs={"class":"pagination pull-right"})
        if not paginator:
            break
        lis = paginator.find_all("li")
        if len(lis) < 2 or lis[-2].has_attr("class") and "disabled" in lis[-2].get("class"):
            break
        a = lis[-2].find("a")
        link = a.get("href")
        if link == "#":
            break
        if len(books) >= max_count > 0:
            break
    return books, tags

def get_text(link):
    text = []
    ua = UserAgent()
    data = requests.get(link, headers={'User-Agent': ua.random})
    data = bs(data.content, "lxml")
    btn = [a.get("href") for a in data.find_all("a") if "ЧИТАТЬ" in a.getText()]
    if len(btn) != 1:
        return
    link = btn[0]
    while True:
        data = requests.get(link, headers={'User-Agent': ua.random})
        data = bs(data.content, "lxml")
        text.append(data.find("article", attrs={"class":"single-blog"}).getText())
        paginator = data.find("ul",attrs={"class":"pagination"})
        if not paginator:
            break
        lis = paginator.find_all("li")
        if len(lis) < 3 or lis[-3].has_attr("class") and "disabled" in lis[-3].get("class"):
            break
        a = lis[-3].find("a")
        link = a.get("href")
        if link == "#":
            break
    return "\n".join(text)

def read_tags(file_name):
    with open(file_name, "r", encoding="utf-8") as f:
        return json.load(f)

def read_book_links(file_name, max_count_by_tag = 0):
    with open(file_name, "r", encoding="utf-8") as f:
        data = json.load(f)
        tags = {}
        books = []
        for book in data:
            if  0 < max_count_by_tag <= min([max_count_by_tag + 1] + [tags.get(tag, 0) for tag in book["categories"]]):
                continue
            books.append(book)
            for tag in book["categories"]:
                tags[tag] = tags.get(tag, 0) + 1
        return books

if __name__ == "__main__":
    books = read_book_links("data.json", max_count_by_tag = 50)
    for book in books:
        title = re.sub(r"[\\\|\/\:\*\?\"\<\>]", "", book["title"]) + ".txt"
        if exists("books/" + title):
            continue
        try:
            text = get_text(book["href"])
            with open("books/" + title, "w", encoding="utf-8") as f:
                f.write(text)
        except:
            with open("errors.log", "a+", encoding="utf-8") as f:
                f.write(book["href"]+"\n")

    #data, tags = get_links()
    #print(tags)
    #with open("data.json", "w", encoding="utf-8") as f:
    #    json.dump(data, f, ensure_ascii=False, indent=4)
    #with open("tags.json", "w", encoding="utf-8") as f:
    #    json.dump(tags, f, ensure_ascii=False, indent=4)
    #b = random.choice(data)
    #text = get_text(b["href"])
    #with open("books/" + b["title"] + ".txt", "w", encoding="utf-8") as f:
    #    f.write(text)