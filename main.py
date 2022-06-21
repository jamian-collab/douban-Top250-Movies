import random
import requests
from bs4 import BeautifulSoup
import jieba
import os
import time
from wordcloud import WordCloud


def wordcloudgenerate(txt, moviename):
    words = jieba.lcut(txt)  # 精确分词
    newtxt = ''.join(words)  # 空格拼接
    wordcloud = WordCloud(font_path="msyh.ttf", max_words=10).generate(newtxt)
    wordcloud.to_file(f'{moviename}热词.jpg')


def get_movie(pagenum):
    # 获取电影
    # pagenum是页数，250部电影，每页25部，一共10页
    Headers = {  # 浏览器头用于伪装爬虫
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) \
            AppleWebKit/537.36 (KHTML, like Gecko) \
                Chrome/102.0.0.0 Safari/537.36'
    }

    # Top250电影的网址
    top250Url = f'https://movie.douban.com/top250?start={pagenum}'
    index = requests.get(url=top250Url, headers=Headers)  # 向服务器提交申请
    soup = BeautifulSoup(markup=index.content,
                         features='html.parser')  # 创建BS实例
    hds = soup.findAll(name='div', attrs={'class': 'hd'})  # 获得该页面的各个电影专栏
    for hd in hds:  # 进行遍历
        time.sleep(3)  # 休眠3秒，防止访问过快IP被豆瓣拉入黑名单
        moviedict = {}

        moviename = hd.find(name='span', attrs={
                            'class': 'title'}).text  # 获取电影名字
        moviedict['moviename'] = moviename
        print(moviename)

        moviehref = hd.find('a')['href']  # 获取电影的链接
        moviedict['moviehref'] = moviehref
        print(moviehref)

        movieinfo = requests.get(url=moviehref, headers=Headers)  # 打开电影专栏
        soup = BeautifulSoup(markup=movieinfo.content,
                             features='html.parser')  # 对电影专栏这一页单独解析
        summary = soup.find(name='span', attrs={
                            'property': 'v:summary'}).text  # 获取概述
        summary = summary.replace(' ', '')  # 去除空格
        summary = summary.replace('\n', '')  # 去除换行
        summary = summary.replace('\u3000', '')  # 去除\u3000字符
        moviedict['summary'] = summary
        print(summary)  # 去除空格

        moviepic = soup.find(name='a', attrs={'class': 'nbgnbg'}).find('img')[
            'src']  # 找到电影封面的链接
        imgbytes = requests.get(url=moviepic, headers=Headers).content  # 下载图片
        with open(f'imgs/{moviename}.jpg', 'wb') as f:
            f.write(imgbytes)  # 写入二进制图片

        rating_right = soup.find(
            name='div', attrs={'class': 'rating_right'})  # 获取打分那一栏
        star_level = int(rating_right.findChild(name='div')[
                         'class'][-1].replace('bigstar', ''))/10  # 获取星级
        moviedict['starlevl'] = star_level
        print(star_level)

        commentUrl = movieinfo.url + 'comments?status=P'
        moviedict['commenturl'] = commentUrl
        print(commentUrl)

        with open('moviesinfo.txt', 'a+', encoding='utf-8') as f:
            # 保存在文本中
            f.write(str(moviedict)+'\n')


def get_wordcloud():
    Headers = {  # 浏览器头用于伪装爬虫
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) \
            AppleWebKit/537.36 (KHTML, like Gecko) \
                Chrome/102.0.0.0 Safari/537.36'
    }

    moviehrefs = []  # 用于存放10部电影的链接
    movienames = []  # 用于存储10部电影的名字
    with open('moviesinfo.txt', 'r+', encoding='utf-8') as f:
        movieinfos = f.readlines()  # 读取多行，每一行都是一部电影
        # 生成十个范围0-249的数字，用于选取随机选取10部电影
        temp = list(range(0, len(movieinfos)))
        random.shuffle(temp)  # 把这个列表打乱
        randomNum = temp[0:10]  # 取打乱的列表的头10个
        for i in randomNum:
            mi = eval(movieinfos[i])  # 字符串转为字典
            moviehrefs.append(mi['moviehref'])  # 将随机电影链接存放在列表中
            movienames.append(mi['moviename'])  # 将随机电影名字存放在列表中

    for moviehref in moviehrefs:
        commenttotal = ''  # 用于保存电影前50的评论
        commentList = []
        for i in range(3):
            time.sleep(3)  # 休眠3秒
            commentUrl = f'{moviehref}comments?start={i*20}'
            comment_res = requests.get(url=commentUrl, headers=Headers)
            soup = BeautifulSoup(markup=comment_res.content,
                                 features='html.parser')
            comments = soup.find_all(name='span', attrs={'class': 'short'})
            for c in comments:
                commentList.append(c.text)
                commenttotal += c.text + '\n'
                if len(commentList) == 50:
                    print(f'{movienames[moviehrefs.index(moviehref)]}的50条评论')
                    print(commentList)
                    # 调用词云生成函数生成词云图片
                    print('生成词云')
                    wordcloudgenerate(
                        commenttotal, movienames[moviehrefs.index(moviehref)])
                    break


if __name__ == '__main__':
    if not os.path.exists('imgs'):  # 创建电影封面的文件夹
        os.mkdir('imgs')
    else:
        os.remove('imgs')
        os.mkdir('imgs')
    if os.path.exists('moviesinfo.txt'):  # 删除电影信息的文本，之后要重新创建
        os.remove('moviesinfo.txt')
    for i in range(2):  # 一共十页
        get_movie(i*25)
    get_wordcloud()
