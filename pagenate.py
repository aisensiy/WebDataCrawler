#!python
# -*- coding: utf8 -*-

from urlparse import urljoin
from crawler import LinkMap, getlisttext
from soupselector import select
from BeautifulSoup import BeautifulSoup
from urllib2 import urlopen

def crawpages(urlp, selector, start=1, limit=-1):
	if urlp.find('%d') == -1: return
	soup = ''
	links = []
	index = start
	
	while True:
		page = urlp % index
		print '-->', page
		new_soup = select(BeautifulSoup(urlopen(urlp % index).read()), selector)
		if new_soup is None or len(new_soup)== 0 or new_soup == soup: 
			print 'repeat or none'
			print 'End at %s' % index
			break
		if limit > 0 and limit + 1 <= index:
			print 'limit ', limit
			print 'End at %s' % index
			break
		print getlisttext(new_soup)
		if(new_soup[0].name == 'a'):
			for link in new_soup:
				if ('href' in dict(link.attrs)):
					url=urljoin(page, link['href'])
					#if url.find("'")!=-1: continue why?
					url=url.split('#')[0] # remove location portion
					if url[0:4]=='http':
						links.append(url)
		else: links.append(page)
		
		soup = new_soup
		index += 1
	
	return links

if __name__ == '__main__':
	url = 'http://coolshell.cn/page/%d'
	selector = 'div#main div h2 a.title'
	crawpages(url, selector)
