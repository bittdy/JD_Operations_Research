# -*- coding: utf-8 -*-
"""
Created on Sun Jul  8 15:07:17 2018

@author: bittdy
"""
import time
import csv
import numpy as np

node = np.zeros((1101,7))
with open('..\..\..\input_node.csv','r') as input_node:
    r = csv.DictReader(input_node)
    for line in r:
        node[int(line['ID'])][0] = line['type']
        node[int(line['ID'])][1] = line['lng                 ']
        node[int(line['ID'])][2] = line['lat                 ']
        if line['type'] == '1':  #起点
            print(line['first_receive_tm'])
            print(line['last_receive_tm'])
            node[int(line['ID'])][3] = 0
            node[int(line['ID'])][4] = 0
            node[int(line['ID'])][5] = time.mktime(time.strptime('1971 '+line['first_receive_tm'],'%Y %H:%M'))
            node[int(line['ID'])][6] = time.mktime(time.strptime('1971 '+'23:59','%Y %H:%M'))+60
        elif line['type'] == '2':#商家
            node[int(line['ID'])][3] = line['pack_total_weight']
            node[int(line['ID'])][4] = line['pack_total_volume']
            node[int(line['ID'])][5] = time.mktime(time.strptime('1971 '+line['first_receive_tm'],'%Y %H:%M'))
            first_time = node[int(line['ID'])][5]
            node[int(line['ID'])][6] = time.mktime(time.strptime('1971 '+line['last_receive_tm'],'%Y %H:%M'))
        elif line['type'] == '3':#充电站
            node[int(line['ID'])][3] = 0
            node[int(line['ID'])][4] = 0
            node[int(line['ID'])][5] = 0
            node[int(line['ID'])][6] = 0
distance_array = np.zeros((1101,1101))
time_array = np.zeros((1101,1101))
with open('..\..\..\input_distance-time.csv','r') as distance_time:
    r = csv.DictReader(distance_time)
    for line in r:
        distance_array[int(line['from_node'])][int(line['to_node'])] = line['distance']
        time_array[int(line['from_node'])][int(line['to_node'])] = int(line['spend_tm'])*60

        #检查是否符合时间窗约束，并返回最大延迟时间



def find_nearest(point_ID):
    min_distance = float('inf')
    charge_index = -1
    for i in range(1001,1101):
        if distance_array[point_ID][i] < min_distance:
            min_distance = distance_array[point_ID][i]
            charge_index = i
    return min_distance,charge_index
serve =  [0, 31538100.0, 0, 987, 1083, 0]

print(time.strftime('%H:%M',time.localtime(31538100.0)))


print(time_array[0][2])
print(time_array[2][0])
print(time_array[1039][0])
print(distance_array[0][2])
print(distance_array[2][0])
print(distance_array[1039][0])






suit_time_window = 1
max_delay = float('inf')
require_advance_time = 0
current_time = serve[1]

for i in range(2,len(serve)):
    if i == 2:
        current_time += time_array[0][serve[i+1]]
        require_advance_time = 0
    #最后一次访问0结点，仅检查硬时间窗，计算最大可延迟时间即可
    elif i == len(serve)-1:
        if current_time > node[serve[i]][6]:
            print('i:',i)
            suit_time_window = 0
            require_advance_time = current_time - node[serve[i]][6]
            max_delay = 0
            break
        else:
            delay_time = node[serve[i]][6] - current_time
            if delay_time < max_delay:
                max_delay = delay_time
            else:
                max_delay = max_delay
            require_advance_time = 0
    #除了第一次和最后一次访问起点，要加上等待时间以及到下一个点的时间
    elif serve[i] == 0 and (i != 2 and i != len(serve)-1):
        if current_time > node[serve[i]][6]:
            print('i:',i)
            suit_time_window = 0
            require_advance_time = current_time - node[serve[i]][6]
            max_delay = 0
            break
        else:
            delay_time = node[serve[i]][6] - current_time
            if delay_time < max_delay:
                max_delay = delay_time
            else:
                max_delay = max_delay
            current_time += 60*60
            current_time += time_array[0][serve[i+1]]
            require_advance_time = 0
    #充电站，充电0.5小时
    elif serve[i] in range(1001,1101):
        if current_time > node[serve[i]][6]:
            print('i:',i)
            suit_time_window = 0
            require_advance_time = current_time - node[serve[i]][6]
            max_delay = 0
            break
        else:
            current_time += 0.5*60*60
            current_time += time_array[serve[i]][serve[i+1]]
            require_advance_time = 0
    #访问商家，卸货，如果早于最早，还要等到最早服务时间
    elif serve[i] in range(1,1001):
        a = time.strftime('%H:%M',time.localtime(current_time))
        b = time.strftime('%H:%M',time.localtime(node[serve[i]][5]))
        if current_time < node[serve[i]][5]:
            delay_time =node[serve[i]][6] - current_time
            if delay_time < max_delay:
                max_delay = delay_time
            else:
                max_delay = max_delay
            current_time = node[serve[i]][5]
            current_time += 0.5*60*60
            current_time += time_array[serve[i]][serve[i+1]]
            require_advance_time = 0
        elif current_time > node[serve[i]][6]:
            print('i:',i)
            suit_time_window = 0
            require_advance_time = current_time - node[serve[i]][6]
            max_delay = 0
            break
        else:
            delay_time = node[serve[i]][6] - current_time
            if delay_time < max_delay:
                max_delay = delay_time
            else:
                max_delay = max_delay
            current_time += 0.5*60*60
            current_time += time_array[serve[i]][serve[i+1]]
            require_advance_time = 0