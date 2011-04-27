#!python
# -*- coding: utf8 -*-

import re

def formatname(name):
	return re.sub(r'[\s*?]+', '', name)

if __name__ == "__main__":
	print formatname(u'围观发 阿飞')

