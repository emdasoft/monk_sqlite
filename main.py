import requests
from bs4 import BeautifulSoup
import re
import time
import datetime
import sqlite3


# подключение к базе данных, она уже создана заранее
conn = sqlite3.connect('monkrus.db')
c = conn.cursor()


# функция для получения тела страницы, html-код:
def get_html(url):
    r = requests.get(url)
    if r.ok:
        return r.text
    print(r.status_code)


# функция получения рейтинга статьи, считает отдельно, т.к. рейтинг подгружается на сайт динамически
# со стороннего ресурса, через jquery-json, но ответ не чисты json, поэтому парсим как строку, т.е. в ответе находим
# подстроку "rating":" и обрезаем до нее плюс 10 символов, чтобы и ее обрезать, образаем конец, т.е. то, что идет после
# самого рейтинга, в итоге имеет строку вида "6:30:11111111", которую сплитим по : на элементы списка, затем через try
# получаем рейтинг (деление второго на первое с округлением до 1 знака)
def get_rating(link):
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 ( \
                                                                KHTML, like Gecko) Chrome/75.0.3770.142 Safari/537.36',
        'Referer': link
        }
    r = requests.get(link, headers=headers)
    data = r.text[r.text.find('"rating":"') + 10:r.text.find('","setting":')].split(':')
    try:
        rating = round((int(data[1]) / int(data[0])), 1)
    except:
        rating = ''
    return rating


def get_data(html, link, rating):
    soup = BeautifulSoup(html, 'lxml')
    title = soup.find('h2', class_='post-title entry-title').text.strip()
    t = soup.find('div', class_='post-header').text.strip().split()
    months = {'января': '01', 'февраля': '02', 'марта': '03', 'апреля': '04', 'мая': '05', 'июня': '06', 'июля': '07',
              'августа': '08', 'сентября': '09', 'октября': '10', 'ноября': '11', 'декабря': '12'}
    s = t[2] + '/' + months[t[3]] + '/' + t[4] + ' ' + t[6]
    publ_time = time.mktime(datetime.datetime.strptime(s, "%d/%m/%Y %H:%M").timetuple())
    r_link = ''
    try:
        rutr = soup.find('div', class_='post-indent').find_all('a')
        for r in rutr:
            if 'http://rutracker' in r.text:
                r_link = r.text.strip()
            else:
                continue
    except:
        r_link = ''

    c.execute('''INSERT INTO articles (title, link, rating, publ_time, r_link) VALUES (?, ?, ?, ?, ?)''', (
                                                                        title, link, rating, publ_time, r_link))
    conn.commit()


def main():

    c.execute("""
        CREATE TABLE articles (
         id INTEGER PRIMARY KEY AUTOINCREMENT,
         title text,
         link text,
         rating text,
         publ_time text,
         r_link text);
        """)
    conn.commit()

    url = 'http://ww9.monkrus.ws/2015/01/blog-post.html'

    pattern = 'Предыдущее'

    while True:
        chan = url.replace('http://ww9.monkrus.ws', '')
        link = 'http://j.cackle.me/widget/58699/bootstrap?chan={}&url={}&callback=cackle_Comment58699'.format(chan, url)
        get_data(get_html(url), url, get_rating(link))
        s = BeautifulSoup(get_html(url), 'lxml')
        try:
            url = s.find('div', class_='blog-pager').find('span', id='blog-pager-older-link').find('a', text=re.compile(
                                                                                                pattern)).get('href')
        except :
            break

    conn.close()


if __name__ == '__main__':
    main()
