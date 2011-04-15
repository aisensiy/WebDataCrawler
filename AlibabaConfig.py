# -*- coding: utf-8 -*-

encode = 'gb2312'
logfile = r'D:\python_sth\test\html\log.log'
workdir = r'D:\python_sth\test\html'
config = [
          {
           'url':'http://page.china.alibaba.com/buy/trade/1.html',
           'selector':'div#vi_fdev_main div#a3_tube_1 div.vi_frame00_04 div.hc_category ul li.dian',
           'keywords':[],
           'title':'css:a.fg2',
           },
           {
            'selector':'ul a',
            'default_selector':'a.fg2',
            'process':lambda s: s.replace('n-y', 's-img_p-%d_cleanCookie-false_offset-10_pageSize-40_n-y'),
            },
            {
#             'collapse': True,
             'selector':'#SearchList .offer .summary'
             }
          ]