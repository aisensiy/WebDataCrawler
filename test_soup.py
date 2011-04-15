# -*- coding: utf8 -*-
from BeautifulSoup import *
from soupselector import select
from urllib2 import urlopen 
import os
import sys
from AlibabaConfig import *

## the web page encode
#encode = 'gb2312'
## log file dir
#logfile = r'D:\python_sth\sina\log.log'
## download file dir
#workdir = r'D:\python_sth\sina'
#config = [
#          {
#           'url':'http://news.sina.com.cn/z/jsyczlswr/1.shtml',
#           'selector':'span.title14 li a',
#           'keywords':[],
#           #'title':'css:span.title14 li a'
#           },
#           {
#            'collapse':True,
#            'selector':''
#            }
#          ]



def keyword_filter(soups, keywords):
    if keywords == None or len(keywords) == 0: return soups;
    new_soups = []
    for soup in soups:
        for keyword in keywords:
            if unicode(soup).find(keyword) != -1:
                new_soups.append(soup)
                break
    return new_soups

def gettextonly(soup):
    v = soup.string
    if v == None:
        c = soup.contents
        resulttext = ''
        for t in c:
            subtext = gettextonly(t)
            resulttext += subtext + ' '
        return resulttext
    else:
        return v.strip()
    
def getlisttext(soups):
    if type(soups) == list:
        resulttext = ''
        for soup in soups:
            resulttext += gettextonly(soup)
    else: return gettextonly(soups)
    
class LinkMap:
    def __init__(self, parent=None, children=None, soup=None, url=None, title=None, level=0, dir=None):
        self.level = level
        self.parent = parent
        self.children = children
        # soup and url always only one exists in the node
        self.soup = soup
        self.url = url
        self.title = title
        self.dir = dir
    
def create_crawl_hierarchy(config):
    map = LinkMap(
                  url=config[0]['url'],
                  dir=workdir
                  )
    create_children(map)
    return map

def create_children(map):
    if map.level >= len(config) - 1:
        return
    current_config = config[map.level]
    if map.url != None:
        soup = BeautifulSoup(urlopen(map.url).read().decode(encode, 'ignore'))
    elif map.soup != None:
        soup = map.soup
    soups = select(soup, current_config['selector'])
    # use keywords as a filter
    if 'keywords' in current_config:
        soups = keyword_filter(soups, current_config['keywords'])
    children = []
    for i in range(len(soups)):
        if soups[i].name == 'a':
#            print soups[i]['href'], soups[i].string
            url = soups[i]['href']
            title = soups[i].string
            if 'process' in current_config: 
                url = current_config['process'](url)
            soup = None

        else:
            if current_config['title'].startswith('css:'):
                title_css = current_config['title'].split(':', 1)[1]
                title = select(soups[i], title_css)[0].string
            else: title = current_config['title']
            url = None
            soup = soups[i]

        if 'collapse' not in current_config or current_config['collapse'] == False:
            dir = os.path.join(map.dir, title)
        else:
            dir = map.dir

        children.append(LinkMap(
                                parent=map, 
                                url=url,
                                soup=soup, 
                                title=title, 
                                level=map.level + 1, 
                                dir=dir))
        
    # when there is no sub links in the title, we should give another link
    if len(children) == 0 and 'default_selector' in current_config.keys():
        soups = select(soup, current_config['default_selector'])	    
        url = soups[0]['href']
        if 'process' in current_config: url = current_config['process'](url)
        if 'collapse' not in current_config or current_config['collapse'] == False:
            dir = os.path.join(map.dir, title)
        else:
            dir = map.dir
        children.append(LinkMap(
                                parent=map, 
                                url=url, 
                                title=soups[0].string, 
                                level=map.level + 1, 
                                dir=dir))
    map.children = children
    
    for child in map.children:
        create_children(child)

def crawl_pages(map):
    if map.children == None:
        if map.url.find('%d') != -1:
            if not file_exist('%s\t%s' % (map.dir, map.url)):
                if not os.path.exists(map.dir):
                    os.mkdir(map.dir)
                    print 'mkdir ', map.dir
                save_pagenates(map)
                file(logfile, 'a').write(map.dir + '\t' + map.url + '\r\n')
            else:
                print '%s is already downloaded.' % (map.title)
        else:
            save_page(map.url, os.path.join(map.dir, map.title + '.html'))
    else:
        if not file_exist('%s\t%s' % (map.dir, map.url)):
            if not os.path.exists(map.dir):
                os.mkdir(map.dir)
                print 'mkdir ', map.dir
            for child in map.children:
                crawl_pages(child)
            file(logfile, 'a').write('%s\t%s\r\n' % (map.dir, map.url))
        else:
            print '%s is already downloaded.' % (map.title)
            
        
def print_mapLink(map, indent):
    print '\t' * indent, map.level, map.title, map.url, map.dir
    if map.children != None:
        for child in map.children:
            print_mapLink(child, indent + 1)
            
def file_exist(line):
    if line in [elem.strip() for elem in open(logfile, 'r')]:
        return True
    return False

def save_pagenates(leaf, limit= -1):
    url_param = leaf.url
    index = 1
    url = url_param % (index)
    filename = os.path.join(leaf.dir, "%s.html" % (index))
    while file_exist("%s\t%s" % (filename, url)):
        print '%s is already downloaded.' % (url)
        index += 1
        url = url_param % (index)
        filename = os.path.join(leaf.dir, "%s.html" % (index))
    page = urlopen(url).read().decode(encode, 'ignore')
    soup = select(BeautifulSoup(page), config[leaf.level]['selector'])
    if soup == None or len(soup) == 0: print 'break 1'; return
    else: print 'page: ', index, getlisttext(soup)
    try:
        file = open(filename, 'w').write(page.encode(encode, 'ignore'))
    except IOError as err:
        print 'error: ', str(err), filename
    open(logfile, 'a').write(filename + '\t' + url + '\r\n')
    index += 1
    url = url_param % (index)
    filename = os.path.join(leaf.dir, "%s.html" % (index))
    while True:
        while file_exist("%s\t%s" % (filename, url)):
            print '%s is already downloaded.' % (url)
            index += 1
            url = url_param % (index)
            filename = os.path.join(leaf.dir, "%s.html" % (index))
        tmp_page = urlopen(url).read().decode(encode, 'ignore')
        tmp_soup = select(BeautifulSoup(tmp_page), config[leaf.level]['selector'])
#        print tmp_soup
#        print tmp_page == page, tmp_soup == soup
        if tmp_page == page or tmp_soup == soup or tmp_soup == None or len(tmp_soup) == 0: print 'break 1'; break
        else: print 'page: ', index, getlisttext(tmp_soup[0])
        try:
            open(filename, 'w').write(tmp_page.encode(encode, 'ignore'))
        except:
            print filename
        open(logfile, 'a').write(filename + '\t' + url + '\r\n')
        page = tmp_page
        soup = tmp_soup
        index += 1
        if limit > 0 and limit < index: break
        url = url_param % (index)
        filename = os.path.join(leaf.dir, "%s.html" % (index))
        
def savePerpage(url, index, dir):
    filename = os.path.join(dir, str(index) + '.html')
    true_url = url % (index)
    page = save_page(true_url, filename)
    return page

def save_page(url, dir):
    if file_exist(dir + '\t' + url):
        print '%s is already downloaded.' % (url)
        return
    
    print dir + '\t' + url
    page = urlopen(url).read()
    open(dir, 'w').write(page)
    file(logfile, 'a').write(str(dir) + '\t' + str(url) + '\r\n')
    return page

if __name__ == '__main__':
    if not os.path.exists(workdir): os.makedirs(workdir)
    if not os.path.exists(logfile): file(logfile, 'w')
    map = create_crawl_hierarchy(config)
    print_mapLink(map, 0)
#    crawl_pages(map)
