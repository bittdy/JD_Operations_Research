# -*- coding: utf-8 -*-
"""
Created on Fri Aug 17 09:12:38 2018

@author: bittdy
"""

import time

a1 = time.mktime(time.strptime('1971:21:14:44','%Y:%H:%M:%S'))
a2 = time.mktime(time.strptime('1971:21:37:37','%Y:%H:%M:%S'))

print(a2-a1)