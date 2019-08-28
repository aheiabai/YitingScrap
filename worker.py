# -*- coding: utf-8 -*-
"""
Spyder Editor

This is a temporary script file.
"""
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from parsel import Selector
import requests
import os
import threading
import pymongo
import logging

            
        

options = Options()
options.headless = True
#browser = webdriver.Chrome(chrome_options=options,
 #                          service_args=["--verbose", "--log-path=chrome.log"])
domain = 'https://www.1ting.com'
localpath = '/Music/1ting/'
url = "https://www.1ting.com/genre/g101p0/song"
url2 = 'https://www.1ting.com/genre/g137p0.html'
url3 = 'https://www.1ting.com/genre/g83p0.html'
url4 = 'https://www.1ting.com/genre/g227p0.html'
url5 = 'https://www.1ting.com/genre/g221p0.html'
url6 = 'https://www.1ting.com/genre/g159p0.html'

dbclient = pymongo.MongoClient('mongodb://admin:404004000@106.13.103.14')
db = dbclient.yiting
songsclt = db.songs


def fetch(url, storepath, songdetail):
    browser = webdriver.Chrome(chrome_options=options,
                           service_args=["--verbose", f"--log-path=chrome.log"])
    browser.get(url)
    """ construct cookie """
    mycookie = ''
    cookies = browser.get_cookies()
    for cookie in cookies:
        name = cookie['name']
        value = cookie['value']
        mycookie += f'{name}={value};'
    print(mycookie)

    innerHTML = browser.execute_script("return document.body.innerHTML")
    #print(innerHTML)
    sel = Selector(innerHTML)
    downloadpages = sel.css('[id^="song-list"]')\
                            .xpath('descendant::a[@target="_1ting"]')
    print(f"number of songs: {len(downloadpages)}")
    
    """ extract mp3 from each downlaodpage and download """
    for element in downloadpages:
        try: 
            page = element.xpath('@href').get()
            songinpage = element.xpath('@title').get()
            """ skip song in db """
            genre = songdetail['genre']
            subgenre = songdetail['subGenre']
            number = songsclt.count_documents({'title': songinpage, 'subGenre': subgenre})
            if number != 0:
                print(f'skipping {songinpage} in db')
                continue
            
            songpage = domain + page
            browser.get(songpage)
            innerHTML = browser.execute_script("return document.documentElement.innerHTML") # get whole document
            sel = Selector(innerHTML)
            
            """ get songinfo and init songdetail """
            songinfo = sel.xpath('//meta[@name="properties"]/@content').get()
            print(songinfo + f" -- {threading.current_thread().name}")
            infolist = songinfo.replace('/',' ').split(',')
            songname = infolist[0]
            author = infolist[1]
            album = infolist[2]
            songdetail['title'] = songname
            songdetail['author'] = author
            songdetail['album'] = album
               
            """ skip song not existing """        
            existence = sel.css('div.listbox').xpath('./ul/h3/text()').get()
            if existence is not None and '该歌曲不存在' in existence:
                #print(f'skip nonexistent song, {songname}: {existence}')
                """ insert a nonexitent song in which value of location is '' """
                songdetail['location'] = ''
                songsclt.insert_one(songdetail)
                print(f'Skip not existing song --> detail:{songdetail}')
                del songdetail['_id']
                continue
            """ skip song that has downloaded """
            downloadedsong = songsclt.find_one({'title': songname, 'author': author, 'album': album})
            if downloadedsong is not None:
                songdetail['location'] = downloadedsong['location']
                songsclt.insert_one(songdetail)
                print(f'Skip downloaded song, location: {downloadedsong["location"]}')
                del songdetail['_id']
                continue
        
            mp3 = sel.css('audio').attrib['src']
            response = requests.get('https:'+mp3, headers={'cookie': mycookie,
                                                       'referer': url})
            #print(response.status_code)
            filename = f'{author}-{songname}.mp3'
            filelocation = storepath + filename
            with open(filelocation, 'wb') as f:
                f.write(response.content)
                
            """ insert record to mongodb """
            songdetail['location'] = filelocation
            songsclt.insert_one(songdetail)
            print(f'Successfully download a song --> detail:{songdetail}')
            del songdetail['_id']
        except Exception as e:
            logging.error(e.msg)
            continue
    browser.quit()
    print('Thread end')

class ChromeShadow(threading.Thread):
    def __init__(self, url, logpath):
        threading.Thread.__init__(self)
        self.url = url
        self.logpath = logpath
    def run(self):
        fetch(self.url, self.logpath)

if __name__ == '__main__':
    c1 = ChromeShadow(url3, 'chrome1.log')
    c2 = ChromeShadow(url4, 'chrome2.log')
    c3 = ChromeShadow(url5, 'chrome3.log')            
    c4 = ChromeShadow(url6, 'chrome4.log')
    
    c1.start()
    c2.start()
    c3.start()
    c4.start()
    
    c1.join()
    c2.join()
    c3.join()
    c4.join()
    print('all end')

