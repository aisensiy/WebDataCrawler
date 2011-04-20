# -*- coding: utf-8 -*-
"""
Here is the config file for crawling alibaba agriculture information.
"""
# give the encoding of web page
encode = 'gb2312'
# the directory of log file, the log file can aviod repeat download
# when you restart the programe
logfile = r'D:\python_sth\test\html\log.log'
# This is where you download the web pages
workdir = r'D:\python_sth\test\html'
# config is a list in python, every item of it is a dictionary. The
# config help create the LinkMap.
config = [
          {
           'url':'http://page.china.alibaba.com/buy/trade/1.html',
		   # selector is a css selector which is used to locate elements in the html
           'selector':'div#vi_fdev_main div#a3_tube_1 div.vi_frame00_04 div.hc_category ul li.dian',
		   # keywords is a filter for elements get by selector
           'keywords':[],
		   # it define the dir name, if the element selected is a a,
		   # then the a's content will be the name if 'title' is not given
           'title':'css:a.fg2',
           },
           {
            'selector':'ul a',
			# if no item can be found by the 'selector, default_selector can be used'
            'default_selector':'a.fg2',
            'process':lambda s: s.replace('n-y', 's-img_p-%d_cleanCookie-false_offset-10_pageSize-40_n-y'),
            },
            {
             'selector':'#SearchList .offer .summary'
             }
          ]
