# -*- coding: utf-8 -*-
"""
Created on Mon Aug 19 07:40:20 2019

@author: ahei
"""

from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from parsel import Selector
import worker
import requests
import os
import threading
from concurrent.futures import ThreadPoolExecutor
import logging

logging.basicConfig(filename='app.log', level=logging.INFO)
pool = ThreadPoolExecutor(max_workers=7)

domain = 'https://www.1ting.com'
localpath = '/Music/1ting/'
url = domain + '/genre'

options = Options()
options.headless = True
browser = webdriver.Chrome(chrome_options=options,
                           service_args=["--verbose", f"--log-path=chrome.log"])
browser.get(url)
innerHTML = browser.execute_script("return document.body.innerHTML")
sel = Selector(innerHTML)
dlgenres = sel.css('.allGenre').xpath('.//dl').getall()
for topgenre in dlgenres:
    
    topsel = Selector(topgenre)
    #topsel = Selector(dlgenres[11])
    genrename = topsel.xpath('//dt/strong/text()').get()
    print(genrename)
    
    """ get all songs of sub genre """
    subgenreurls = topsel.xpath('//ul/li/a/@href').getall()
    #print(subgenreurls)
    subgenrenames = topsel.xpath('//ul/li/a/text()').getall()
    #print(subgenrenames)
    for index, suburl in enumerate(subgenreurls):
        subgenrename = subgenrenames[index].replace("/", " ")
        storepath = f'{localpath}{genrename}/{subgenrename}/'
        
        allsongurl = domain + suburl.replace('.html', '/song')
        browser.get(allsongurl)
        innerHTML = browser.execute_script("return document.body.innerHTML")
        subsel = Selector(innerHTML)
        downlaodpages = subsel.xpath('//li[has-class("thispage")]//a/@href|//li[has-class("pageitem")]//a/@href').getall()
        print(storepath, len(downlaodpages))
        
        """ start worker downlaoding songs for each sub genre page """
        for page in downlaodpages: 
            if not os.path.exists(storepath):
                os.makedirs(storepath)
            songinfo = {'genre': genrename,
                        'subGenre': subgenrenames[index],
                        'title': '董小姐',
                        'author': '宋东野',
                        'album': '安河桥北',
                        'location': '/Music/1ting/Pop/Hip-Hop/dongxiaojie.mp3',
                        'duration': 240}
            pageurl = domain + page
            pool.submit(worker.fetch, *(pageurl, storepath, songinfo))
            #worker.fetch(pageurl, storepath, songinfo)
browser.quit()
pool.shutdown()
print('End')
