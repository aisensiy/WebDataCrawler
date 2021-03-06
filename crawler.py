# -*- coding: utf8 -*-
"""
This is the core of crawler(or even say this is the whole crawler
right now, I will add new features for it.) and it's main creative
feature is that it can crawler the web pages according to the config
file and create a hierarchy like:
	Item 1
		Item 1.1
			html files belong to Item 1.1
		Item 1.2
			html files belong to Item 1.2
		...
The hierarchy gives the info of classification which is quite
estimable for our futhure work. 
The crawle action right now contains two steps.
step 1.	create the crawle hierarchy according to the config
		dictionary, the hierarchy in the Python code is a big LinkMap,
		a tree like data structure.
step 2. crawle web pages under the structure of LinkMap. It knows
		when to create a directory, when stop crawle and change to
		another directory.
Up to now, It works well on crawling Alibaba data. 
"""

from BeautifulSoup import *
from soupselector import select
from urllib2 import urlopen 
import pagenate
import os
import sys
import utils

#from AlibabaConfig import *
from common import *

# the web page encode
# encode = 'gb2312'
# log file dir
# logfile = '/home/aisensiy/html/sina/log.log'
# download file dir
# workdir = '/home/aisensiy/html/sina'
# config = [
# 		  {
# 		   'url':'http://roll.news.sina.com.cn/s_zjkywr_all/1/index.shtml',
# 		   'selector':'div#d_list ul li span.c_tit a',
# 		   'keywords':[],
# 		   'collapse':True
# 		   #'title':'css:span.title14 li a'
#		   },
#		   {}
#		  ]
#

# here the 'keywords is used as a filter'
def keyword_filter(soups, keywords):
	"""as a filter to filte the soup which no keyword is included"""
	if keywords == None or len(keywords) == 0: 
		return soups;
	new_soups = []
	for soup in soups:
		for keyword in keywords:
			if unicode(soup).find(keyword) != -1:
				new_soups.append(soup)
				break
		return new_soups

def gettextonly(soup):
	"""Get the text from html"""
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
	"""transform a list or a soup into plain text"""
	if type(soups) == list:
		resulttext = ''
		for soup in soups:
			resulttext += gettextonly(soup) + '\n'
		return resulttext
	else: return gettextonly(soups)
	
# represent the hierarchy
class LinkMap:
	def __init__(self, parent=None, children=None, soup=None, url=None, title=None, level=0, dir=None, selector=None):
		self.level = level
		self.parent = parent
		self.children = children
		self.selector = selector
		# soup and url always only one exists in the node
		self.soup = soup
		self.url = url
		# title will be the name of the directory which is represented by the LinkMap object
		self.title = title
		# the dir path 
		self.dir = dir
	
def create_crawl_hierarchy(config):
	"""the hierarchy is created according to the config"""
	map = LinkMap(
				  url=config[0]['url'],
				  dir='html',
				  selector=config[0]['selector']
				  )
	create_children(map)
	return map

def create_children(map):
	if map.level >= len(config) - 1:
		return
	current_config = config[map.level]

	# here we create soup by url or soup from the parent 'map'
	if map.url != None:
		soup = BeautifulSoup(urlopen(map.url).read().decode(encode, 'ignore'))
	elif map.soup != None:
		soup = map.soup
	# we use the 'selector' to create html fragments we called soups
	soups = select(soup, current_config['selector'])
	# use keywords as a filter
	if 'keywords' in current_config:
		soups = keyword_filter(soups, current_config['keywords'])
		
	children = []
	for i in range(len(soups)):
		# if the element is 'a' then we record url and make soup None,
		# if the element is sth else, we make url None and soup the
		# elements.
		if soups[i].name == 'a':
#		   print soups[i]['href'], soups[i].string
			url = soups[i]['href']
			# use the content as the title
			title = soups[i].string
			# if process is in the config, we will use it for url
			# transformation.
			if 'process' in current_config: 
				url = current_config['process'](url)
			soup = None
		else:
			# if the name is not 'a', we may use the 'title' in
			# config, if 'title' startswith 'css:', we will use the
			# element's content as the title, or we use the 'title'
			# config directly.
			if current_config['title'].startswith('css:'):
				title_css = current_config['title'].split(':', 1)[1]
				title = select(soups[i], title_css)[0].string
			else: title = current_config['title']
			url = None
			soup = soups[i]

		# if 'collapse' is True then, it will not create a new dir
		# with title as its name
		if 'collapse' not in current_config or current_config['collapse'] == False:
			if map.dir is None or map.dir == '': dir = title
			else: dir = os.path.join(map.dir, title)
		else:
			dir = map.dir

		children.append(LinkMap(
								parent=map, 
								url=url,
								soup=soup, 
								seletor=config[map.level + 1]['selector'],
								title=title, 
								level=map.level + 1, 
								dir=utils.formatname(dir)))
		
	# when there is no sub links in the title, we should give another
	# link, use the 'default_selector'
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
								seletor=config[map.level + 1]['selector'],
								title=soups[0].string, 
								level=map.level + 1, 
								dir=utils.formatname(dir)))
	map.children = children
	
	for child in map.children:
		create_children(child)

def crawl_pages(map):
	"""Here we crawle pages according to the LinkMap"""
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
			if not file_exist('%s\t%s' % (map.dir, map.url)):
				if not os.path.exists(map.dir):
					os.mkdir(map.dir)
					print 'mkdir ', map.dir
				save_page(map.url, os.path.join(map.dir, map.title + '.html'))
				file(logfile, 'a').write(map.dir + '\t' + map.url + '\r\n')
			else:
				print '%s is already downloaded.' % (map.title)
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
			
		
def print_linkmap(map, indent):
	"""print the linkmap for debug or test"""
	print '\t' * indent, map.level, map.title, map.url, map.dir
	if map.children != None:
		for child in map.children:
			print_linkmap(child, indent + 1)
			
def file_exist(line):
	"""test if the url or dir is downloaded"""
	if line in [elem.strip() for elem in open(logfile, 'r')]:
		return True
	return False

def save_pagenates(leaf, limit= -1):
	"""抓取有分页的url，他们的URL大多类似"""
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
		print tmp_soup
		print tmp_page == page, tmp_soup == soup
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
		
def save_page(url, dir):
	"""download a single page"""
	if file_exist(dir + '\t' + url):
		print '%s is already downloaded.' % (url)
		return
	
	print dir + '\t' + url
	page = urlopen(url).read()
	open(dir, 'w').write(page)
	file(logfile, 'a').write(str(dir) + '\t' + str(url) + '\r\n')
	return page

def run_crawl(workdir, logfile, config, test=False):
	if not os.path.exists(workdir): os.makedirs(workdir)
	if not os.path.exists(logfile): file(logfile, 'w')
	map = create_crawl_hierarchy(config)
	print_linkmap(map, 0)
	if not test: crawl_pages(map)

def createlinks(config, linkmap, filename):
	if linkmap.children is None or len(linkmap.children) == 0:
		if linkmap.url.find('%d') == -1:
			print '-1'
			open(filename, 'a').write("%s\t%s\r\n" % (linkmap.url, linkmap.dir))
		else:
			links = pagenate.crawpages(linkmap.url, linkmap.selector, limit=10)
			for link in links:
				open(filename, 'a').write("%s\t%s\r\n" % (link, linkmap.dir))
	else:
		for child in linkmap.children:
			createlinks(child, filename)

if __name__ == "__main__":
#	run_crawl(workdir, logfile, config, True)
	linkmap = create_crawl_hierarchy(config)
	print_linkmap(linkmap, 0)
	createlinks(config, linkmap, 'links.txt')
