import requests
import random
import base64
from Crypto.Cipher import AES
import json
import binascii
from bs4 import BeautifulSoup as BS
import os
import time


class Music_Api:
    # 设置从JS文件提取的RSA的模数、协商的AES对称密钥、RSA的公钥等重要信息
    def __init__(self):
        self.modulus = "00e0b509f6259df8642dbc35662901477df22677ec152b5ff68ace615bb7b725152b3ab17a876aea8a5aa76d2e417629ec4ee341f56135fccf695280104e0312ecbda92557c93870114af6c9d05c4f7f0c3685b7a46bee255932575cce10b424d813cfe4875d3e82047b97ddef52741d546b8e289dc6935b3ece0462db0a22b8e7"
        self.nonce = '0CoJUm6Qyw8W8jud'
        self.pubKey = '010001'
        self.url = "https://music.163.com/weapi/cloudsearch/get/web?csrf_token="
        self.header = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; WOW64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/75.0.3770.100 Safari/537.36',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3',
        }
        self.file_path = './music'
        if not os.path.exists(self.file_path):
            os.makedirs(self.file_path)
        self.secKey = self.getRandom()

    # 生成16字节即256位的随机数
    def getRandom(self):
        string = "1234567890abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ"
        res = ""
        for i in range(16):
            res += string[int(random.random() * 62)]
        return res

    # AES加密，用seckey对text加密
    def aesEncrypt(self, text, secKey):
        pad = 16 - len(text) % 16
        text = text + pad * chr(pad)
        encryptor = AES.new(secKey.encode('utf-8'), 2, '0102030405060708'.encode('utf-8'))
        ciphertext = encryptor.encrypt(text.encode('utf-8'))
        ciphertext = base64.b64encode(ciphertext).decode("utf-8")
        return ciphertext

    # 快速模幂运算，求 x^y mod mo
    def quickpow(self, x, y, mo):
        res = 1
        while y:
            if y & 1:
                res = res * x % mo
            y = y // 2
            x = x * x % mo
        return res

    # rsa加密
    def rsaEncrypt(self, text, pubKey, modulus):
        text = text[::-1]
        a = int(binascii.hexlify(str.encode(text)), 16)
        b = int(pubKey, 16)
        c = int(modulus, 16)
        rs = self.quickpow(a, b, c)
        return format(rs, 'x').zfill(256)

    # 设置相应的请求参数，从而搜索列表
    # 总体的密码加密步骤为：
    # 首先用nonce对text加密生成密文1
    # 然后用随机数seckey加密密文1生成密文2
    # 随后，用公钥加密seckey生成密文3
    # 其中，密文2作为请求参数中的params，密文3作为encSeckey字段
    # 这样，接收方可以通过私钥解密密文3获得seckey(随机数)
    # 然后用seckey解密密文2获得密文1
    # 最终用统一协商的密钥nonce解密密文1最终获得text
    def search(self, s, offset, type):
        text = {
            "hlpretag": "<span class=\"s-fc7\">",
            "hlposttag": "</span>",
            "#/discover": "",
            "s": s,
            "type": type,
            "offset": offset,
            "total": "true",
            "limit": "30",
            "csrf_token": ""
        }
        text = json.dumps(text)
        params = self.aesEncrypt(self.aesEncrypt(text, self.nonce), self.secKey)
        encSecKey = self.rsaEncrypt(self.secKey, self.pubKey, self.modulus)
        data = {
            'params': params,
            'encSecKey': encSecKey
        }
        response = requests.post(url=self.url, data=data, headers=self.header).json()
        return response

    # 通过不同的type以及获得的response获取歌曲id
    def get_playlist(self, response, type):
        if type == '1':
            result = response['result']['song']
            id_list = []
            for result in result:
                id = result['id']
                name = result['name']
                id_list.append((name, id))
            return id_list
        if type == '1000':
            result = response['result']['playlists']
            id_list = []
            for result in result:
                id = result['id']
                id_list.append(id)
        song_list = []
        for id_list in id_list:
            url = 'https://music.163.com/playlist?id=' + str(id_list)
            response = requests.get(url, headers=self.header).content
            s = BS(response, 'lxml')
            html = s.find('ul', {'class': 'f-hide'})
            results = html.find_all('a')
            for result in results:
                song_name = result.text
                song_id = result["href"]
                song_id = song_id.replace('/song?id=', '')
                song_list.append((song_name, song_id))
        return song_list

    # 通过获取的歌曲id下载歌曲
    def load_music(self, song_list):
        basic_url = 'http://music.163.com/song/media/outer/url?id={}.mp3'
        for song_name, song_id in song_list:
            download_url = basic_url.format(song_id)
            song = requests.get(download_url, headers=self.header)
            time.sleep(1)
            music_path = '{}/{}.{}'.format(self.file_path, song_name, 'mp3')
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

    # 设置一个启动函数
    def run(self):
        s = input('请输入搜索关键字：')
        offset = input('请输入需要爬取的页面数：')
        type_list = input('请输入爬取的类别：')
        if type_list == '歌单':
            type = '1000'
        elif type_list == '歌曲':
            type = '1'
        response = self.search(s, offset, type)
        song_list = self.get_playlist(response, type)
        self.load_music(song_list)


if __name__ == '__main__':
    Music_Api().run()
