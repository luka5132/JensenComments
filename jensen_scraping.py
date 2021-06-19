# -*- coding: utf-8 -*-
"""
Created on Thu Jun 17 10:40:39 2021

@author: luka5132
"""
import os
import selenium
from selenium import webdriver
from selenium.webdriver.common.by import By
import time
from PIL import Image
import io
import requests
from webdriver_manager.chrome import ChromeDriverManager
from selenium.common.exceptions import ElementClickInterceptedException
import re
import pandas as pd
from datetime import datetime
from bs4 import BeautifulSoup
import requests
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.support.wait import WebDriverWait
import selenium.webdriver.support.expected_conditions as EC


JENSEN_SITEMAP = 'https://www.jensen.nl/sitemap.xml'
go = False
search_url="https://jensen.nl/een-grote-grap-de-jensen-show-354"


def get_all_links(sitemap = JENSEN_SITEMAP):
    page = requests.get(sitemap)
    soup = BeautifulSoup(page.content, 'html.parser')
    all_links = soup.find_all('loc')
    link_list = []
    
    unt_video = True
    at_video = True
    i = 0
    while unt_video or at_video:
        c_link = str(all_links[i])
        c_link = re.search('>(.*?)/<', c_link).group(1)
        end_is_digit = re.search(r'\d+$', c_link)
        if end_is_digit:
            at_video = True
            unt_video = False
            link_list.append(c_link)
        else:
            at_video = False
            
        i += 1
    return link_list
        

def get_comments(url):
    driver = webdriver.Chrome(ChromeDriverManager().install())
    driver.get(url.format(q='Car'))
    time.sleep(4)
    driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
    comments = driver.find_elements_by_xpath('//*[@class="commento-card"]')
    driver.close()
    return comments

def find_comment_id(in_html):
    option_str = 'commento-comment-options-'
    opt_len = len(option_str)
    op_ind = in_html.index(option_str)
    ind = op_ind +opt_len
    next_char = in_html[ind]
    comment_id = ''
    while next_char != '"':
        comment_id += next_char
        ind += 1
        next_char = in_html[ind]
    return comment_id

def comment_info(comment_id, html):
    html = html.replace('\n', '')
    score_ind = html.index('"commento-score"')
    timeago_text = '"commento-comment-timeago-{}"'.format(comment_id)
    timeago_ind = html.index(timeago_text)
    text_ind = html.index('"commento-comment-text-{}"'.format(comment_id))
    name_ind = html.index('"commento-name"')
    
    score = re.search('>(.*?)<', html[score_ind:]).group(1)
    #print(score)
    timeago = re.search('"(.*?)"', html[timeago_ind + len(timeago_text):]).group(1)
    #print(timeago)
    text = re.search('<p>(.*?)</p>',html[text_ind:]).group(1)
    #print(text)
    name = re.search('>(.*?)<',html[name_ind:]).group(1)
    #print(name)
    return[score,timeago,text,name]
    #class="commento-name" style="max-width: 126.4000015258789px;">Jack Schlangen</div>
        
    
COLNAMES = ['gen_id','username','body','points','children','parents','date','date_retrieved']
def proc_all_comments(comment_list, column_names = COLNAMES):
    video_comment_df = pd.DataFrame(columns = column_names)
    c_time = datetime.now()
    children_dict = {}
    
    for elem in comment_list:
        html = elem.get_attribute('innerHTML')
        children = elem.find_elements_by_class_name("commento-card")
        cmt_id = find_comment_id(html)
        score, tim, text, username = comment_info(cmt_id,html) # score, time, body, username
        children_string = ''
        children_list =[]
        if children:
            for child in children:
                child_id = find_comment_id(child.get_attribute('innerHTML'))
                children_string += ";{}".format(child_id)
                children_list.append(child_id)
                
        if children_list:
            for child in children_list:
                children_dict[child] = cmt_id
        if cmt_id in children_dict:
            parent_id = children_dict[cmt_id]
        else:
            parent_id = ''
        
        newrow = [cmt_id,username,text,score,children_string,parent_id,tim,c_time]
        video_comment_df.loc[len(video_comment_df)] = newrow
    return video_comment_df

def page_metadata(url):
    page = requests.get(url)
    soup = BeautifulSoup(page.content, 'html.parser')
    h1_raw = str(soup.select('h1'))
    upload_time_raw = str(soup.select('time'))
    h1 = re.search('>(.*?)<', h1_raw).group(1)
    upload_time = re.search('"(.*?)"', upload_time_raw).group(1)
    vid_name,vid_number = h1.split('#')
    
    return [vid_name,vid_number,upload_time]


ALL_COLNAMES = COLNAMES + ['video_name','video_number','video_upload_time']

chrome_options = Options()
chrome_options.add_argument("--headless")
def collect_all_comments():
    full_df = pd.DataFrame(columns = ALL_COLNAMES)
    all_links = get_all_links()
    for link in all_links:
        try:
            driver = webdriver.Chrome(ChromeDriverManager().install(), options = chrome_options)
            driver.get(link.format(q='Car'))
            time.sleep(4)
            driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
            comments = driver.find_elements_by_xpath('//*[@class="commento-card"]')
            vid_name,vid_number,upload_time = page_metadata(link)
            comment_df = proc_all_comments(comments)
            driver.close()
            n_comments = len(comments)
            v_name_list = [vid_name] * n_comments
            v_numb_list = [vid_number] * n_comments
            upload_list = [upload_time] * n_comments
            comment_df['video_name'] = v_name_list
            comment_df['video_number'] = v_numb_list
            comment_df['video_upload_time'] = upload_list
            full_df = full_df.append(comment_df, ignore_index=True)
            print('Finished with: {}'.format(vid_number))

        except:
            pass
        
    full_df.to_csv('jensen_comments.csv')
    return full_df

newgo = False
if newgo:
    URL = "https://jensen.nl/een-grote-grap-de-jensen-show-354"
    page = requests.get(URL)
    soup = BeautifulSoup(page.content, 'html.parser')
    print(soup)

#"commento-score"
#class="commento-score">3 points</div>
#"commento-comment-timeago-a7762c2967fbcd491bf43a31b4bb405712dcc08a7575dc5016a304be0dd9edc1"
#id="commento-comment-timeago-a7762c2967fbcd491bf43a31b4bb405712dcc08a7575dc5016a304be0dd9edc1" title="Wed Jun 16 2021 16:40:05 GMT+0200 (Central European Summer Time)"
#commento-comment-text-a7762c2967fbcd491bf43a31b4bb405712dcc08a7575dc5016a304be0dd9edc1"


########### Within 'commento-header'
#classname =    commento-name
#               commento-score
#               time is more difficult (tille - "EXACT TIME")

######## TEXT within body
    
# date
# profile name
# upvotes
# text
# video name
# video upload date
# video number
# comment id (number)