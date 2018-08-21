# -*- coding: utf-8 -*-
"""
Created on Fri Aug 17 16:19:29 2018

@author: bittdy
"""
import csv

id = 5

data = {1:1601,2:1501,3:1401,4:1301,5:1201}
charge_begin_index = {1:1501,2:1401,3:1301,4:1201,5:1101}

all = [n for n in range(id*10000 + 1,id*10000 + charge_begin_index[id])]
#print(all)

#with open('..\..\Result_'+str(id)+'.csv','r') as input_node:
with open('..\..\Result_5_67.0.csv','r') as input_node:
    r = csv.DictReader(input_node)
    for line in r:
        str_origin = line['dist_seq']
        #print(str_origin)
        str_list = str_origin.split(';')
        #print(str_list)
        for item in str_list:
#            print(item)
            if item == '0':
                continue
            else:
                fin = int(item)
#                print(charge_begin_index[id])
                if fin>=id*10000 + charge_begin_index[id]:
                    continue
                all.remove(fin)
    for i in all:
        print(i)