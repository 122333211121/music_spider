import requests
import os
import time
from bs4 import BeautifulSoup as BS

SONG_LIST = []
file_path = './music'
if not os.path.exists(file_path):
    os.makedirs(file_path)


def get_the_page():
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; WOW64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/75.0.3770.100 Safari/537.36',
        'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3',
    }

    url = 'https://music.163.com/discover/toplist?id=3778678'
    response = requests.get(url, headers=headers).content
    s = BS(response, 'lxml')
    html = s.find('ul', {'class': 'f-hide'})
    results = html.find_all('a')
    for result in results:
        song_name = result.text
        song_id = result["href"]
        song_id = song_id.replace('/song?id=', '')
        SONG_LIST.append((song_name, song_id))


def get_the_music():
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; WOW64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/75.0.3770.100 Safari/537.36',
    }
    basic_url = 'http://music.163.com/song/media/outer/url?id={}.mp3'
    for song_name, song_id in SONG_LIST:
        download_url = basic_url.format(song_id)
        song = requests.get(download_url, headers=headers)
        # print(song)
        time.sleep(1)
        music_path = '{}/{}.{}'.format(file_path, song_name, 'mp3')
        try:
            if not os.path.exists(music_path):
                with open(music_path, 'wb')as f:
                    f.write(song.content)
                    print('{}下载成功'.format(song_name))
                    time.sleep(0.5)

            else:
                print('{}已经下载'.format(song_name))
        except:
            print('{}下载失败'.format(song_name))


def main():
    get_the_page()
    get_the_music()


if __name__ == '__main__':
    main()