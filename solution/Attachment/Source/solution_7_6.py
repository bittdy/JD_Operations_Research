# -*- coding: utf-8 -*-
"""
Created on Sun Jun 24 10:51:00 2018

@author: bittdy
"""
import csv
import numpy as np
import time
#import os

class solution(object):
    def __init__(self):   
        #读取相关数据
        #时间统一为秒，距离统一为米
        #file_path = os.getcwd()
        self.assign_list = []
        #维护两个一维数组，一个记录每个点在哪个列表里，为-1则没分配，另一个记录该点在哪个assign_list中
        record_list = [-1]*1000
        record_ind = [n for n in range(1000)]
        self.record_assign_array = np.array(record_list)
        self.record_index = np.array(record_ind)
        #维护一个二维数组，记录节约值
        self.record_conser = np.zeros((1000,1000))
        
        self.distance_array = np.zeros((1101,1101))
        self.time_array = np.zeros((1101,1101))
        with open('..\..\..\input_distance-time.csv','r') as distance_time:
            r = csv.DictReader(distance_time)
            for line in r:
                self.distance_array[int(line['from_node'])][int(line['to_node'])] = line['distance']
                self.time_array[int(line['from_node'])][int(line['to_node'])] = int(line['spend_tm'])*60
        #print(self.distance[5][6],self.time[7][8])
        
        self.node = np.zeros((1101,7))
        with open('..\..\..\input_node.csv','r') as input_node:
            r = csv.DictReader(input_node)
            for line in r:
                self.node[int(line['ID'])][0] = line['type']
                self.node[int(line['ID'])][1] = line['lng                 ']
                self.node[int(line['ID'])][2] = line['lat                 ']
                if line['type'] == '1':  #起点
                    print(line['first_receive_tm'])
                    print(line['last_receive_tm'])
                    self.node[int(line['ID'])][3] = 0
                    self.node[int(line['ID'])][4] = 0
                    self.node[int(line['ID'])][5] = time.mktime(time.strptime('1971 '+line['first_receive_tm'],'%Y %H:%M'))
                    self.node[int(line['ID'])][6] = time.mktime(time.strptime('1971 '+'23:59','%Y %H:%M')) + 60
                elif line['type'] == '2':#商家
                    self.node[int(line['ID'])][3] = line['pack_total_weight']
                    self.node[int(line['ID'])][4] = line['pack_total_volume']
                    self.node[int(line['ID'])][5] = time.mktime(time.strptime('1971 '+line['first_receive_tm'],'%Y %H:%M'))
                    first_time = self.node[int(line['ID'])][5]
                    self.node[int(line['ID'])][6] = time.mktime(time.strptime('1971 '+line['last_receive_tm'],'%Y %H:%M'))
                    #加一步判断，如果1号车不能满足初始派2号车
                    if first_time-self.time_array[0][int(line['ID'])]<time.mktime(time.strptime('1971 8:00','%Y %H:%M')):
                        self.assign_list.append([0,time.mktime(time.strptime('1971 8:00','%Y %H:%M')),0,int(line['ID']),0])#若出发时间早于8点，则定为8点
                    else:
                        self.assign_list.append([0,first_time-self.time_array[0][int(line['ID'])],0,int(line['ID']),0])  #出发时间定为最晚的不让每个客户等待的时间
                elif line['type'] == '3':#充电站
                    self.node[int(line['ID'])][3] = 0
                    self.node[int(line['ID'])][4] = 0
                    self.node[int(line['ID'])][5] = 0
                    self.node[int(line['ID'])][6] = 0
#        print(self.node[0][6])
        
        self.vehicle = np.zeros((2,6))
        with open('..\..\..\input_vehicle_type.csv','r') as vehicle_type:
            r = csv.DictReader(vehicle_type)
            for line in r:
                self.vehicle[int(line['vehicle_type_ID      '])-1][0] = line['max_volume              ']
                self.vehicle[int(line['vehicle_type_ID      '])-1][1] = line['max_weight              ']
                self.vehicle[int(line['vehicle_type_ID      '])-1][2] = line['driving_range']
                self.vehicle[int(line['vehicle_type_ID      '])-1][3] = line['charge_tm']
                self.vehicle[int(line['vehicle_type_ID      '])-1][4] = line['unit_trans_cost   ']
                self.vehicle[int(line['vehicle_type_ID      '])-1][5] = line['vehicle_cost   ']
        #print(self.vehicle[1][4])
        #print(self.assign_list)
        #p = self.cal_cost([1,31550000.0,2,0])
        #print(p)
        #构造解时，先找距离约束，再算时间约束
        for p in range(len(self.assign_list)):
            distance_flag,time_window_flag,new_serve = self.construct_init(self.assign_list[p])
            self.assign_list[p] = new_serve
            if distance_flag == 0 or time_window_flag == 0:
                print('origin:',self.assign_list[p])
                print('distance_flag:',distance_flag)
                print('time_window_flag:',time_window_flag)
                print('new_serve:',new_serve)
    #record_assign_array中的元素有三个类型
    #-1：未在已构成回路中
    #0：在已构成回路中，为线路内点，不可相连
    #1：在已构成回路中，左边与车场相连
    #2：在已构成回路中，右边与车场相连          
#    def cw_conservation(self):
#
#                    
#                
#        print(self.assign_list)
        
    def convert_vali(self,serve):
        #检查是否符合载货量要求，是否需要用大载重车辆
        suit_volume = suit_weight = suit_time_window = suit_distance = 1
        suit_volume,suit_weight = self.check_weight_volume(serve)
        if serve[0] == 0 and (suit_volume == 0 or suit_weight == 0):
            serve[0] = 1
            suit_volume,suit_weight = self.check_weight_volume(serve)
            if suit_volume == 0 or suit_weight == 0:
                return [suit_volume,suit_weight,suit_time_window,suit_distance],serve
        #检查是否满足时间窗约束，是否能够通过提前出发时间使之可行
        start_time = serve[1]
        suit_time_window,max_delay,require_advance_time =  self.check_time_window(serve,0)
        start_time = serve[1] - require_advance_time
        if suit_time_window == 0:
            while(start_time-require_advance_time > time.mktime(time.strptime('1971 8:00','%Y %H:%M'))):
                suit_time_window,max_delay,require_advance_time =  self.check_time_window(serve,require_advance_time)
                start_time = start_time - require_advance_time
                if suit_time_window == 1:
                    break
        if suit_time_window == 0:
            #提前到8点仍不符合
            return [suit_volume,suit_weight,suit_time_window,suit_distance],serve
        else:
            serve[1] = start_time
        #检查是否符合里程约束，是否能够通过添加充电站使之可行，添加使成本最小的充电站
        suit_distance,serve = self.check_distance(serve,max_delay)
        return [suit_volume,suit_weight,suit_time_window,suit_distance],serve
              
    def check_time_window(self,serve,advance_time):
        #检查是否符合时间窗约束，并返回最大延迟时间
        suit_time_window = 1
        max_delay = float('inf')
        require_advance_time = 0
        current_time = serve[1]
        
        for i in range(2,len(serve)):
            #第一次访问0结点，仅减去时间
            if i == 2:
                current_time += self.time_array[0][serve[i+1]]
                require_advance_time = 0
            #最后一次访问0结点，仅检查硬时间窗，计算最大可延迟时间即可
            elif i == len(serve)-1:
                if current_time > self.node[serve[i]][6]:
                    print('i:',i)
                    suit_time_window = 0
                    require_advance_time = current_time - self.node[serve[i]][6]
                    max_delay = 0
                    break
                else:
                    delay_time = self.node[serve[i]][6] - current_time
                    if delay_time < max_delay:
                        max_delay = delay_time
                    else:
                        max_delay = max_delay
                    require_advance_time = 0
            #除了第一次和最后一次访问起点，要加上等待时间以及到下一个点的时间
            elif serve[i] == 0 and (i != 2 and i != len(serve)-1):
                if current_time > self.node[serve[i]][6]:
                    print('i:',i)
                    suit_time_window = 0
                    require_advance_time = current_time - self.node[serve[i]][6]
                    max_delay = 0
                    break
                else:
                    delay_time = self.node[serve[i]][6] - current_time
                    if delay_time < max_delay:
                        max_delay = delay_time
                    else:
                        max_delay = max_delay
                    current_time += 60*60
                    current_time += self.time_array[0][serve[i+1]]
                    require_advance_time = 0
            #充电站，充电0.5小时
            elif serve[i] in range(1001,1101):
                current_time += 0.5*60*60
                current_time += self.time_array[serve[i]][serve[i+1]]
                require_advance_time = 0
            #访问商家，卸货，如果早于最早，还要等到最早服务时间
            elif serve[i] in range(1,1001):
                if current_time < self.node[serve[i]][5]:
                    delay_time = self.node[serve[i]][6] - current_time
                    if delay_time < max_delay:
                        max_delay = delay_time
                    else:
                        max_delay = max_delay
                    current_time = self.node[serve[i]][5]
                    current_time += 0.5*60*60
                    current_time +=self. time_array[serve[i]][serve[i+1]]
                    require_advance_time = 0
                elif current_time > self.node[serve[i]][6]:
                    print('i:',i)
                    suit_time_window = 0
                    require_advance_time = current_time - self.node[serve[i]][6]
                    max_delay = 0
                    break
                else:
                    delay_time = self.node[serve[i]][6] - current_time
                    if delay_time < max_delay:
                        max_delay = delay_time
                    else:
                        max_delay = max_delay
                    current_time += 0.5*60*60
                    current_time += self.time_array[serve[i]][serve[i+1]]
                    require_advance_time = 0
        return suit_time_window,max_delay,require_advance_time
    
    def check_weight_volume(self,serve):
        suit_volume = suit_weight = 1
        volume = weight = 0
        for i in range(2,len(serve)):
            if self.node[serve[i]][0] == 2:
                weight += self.node[serve[i]][3]
                volume += self.node[serve[i]][4]
        if weight > self.vehicle[serve[0]][1]:
            suit_weight = 0
        if volume > self.vehicle[serve[0]][0]:
            suit_volume = 0
        return suit_volume,suit_weight
    
#    def check_distance(self,serve,max_delay):
#        sum_distance = 0
#        suit_distance = 1
#        for i in range(2,len(serve)-1):
#            sum_distance += self.distance_array[serve[i]][serve[i+1]]
#            if sum_distance > self.vehicle[serve[0]][2]:
#                index = i
#                min_cost = float('inf')
#                min_index = -1
#                for j in range(1001,1101):
#                    cost = self.distance_array[serve[index]][j] + self.distance_array[j][serve[index+1]]
#                    time = self.time_array[serve[index]][j] + self.time_array[j][serve[index+1]] + 0.5*60*60
#                    if time-self.time_array[serve[i]][j] > max_delay:
#                        continue
#                    else:
#                        if cost < min_cost:
#                            min_cost = cost
#                            min_index = j
#                if min_index != -1 and min_cost < self.vehicle[serve[0]][2]:
#                    #有符合时间约束的充电站可以添加
#                    serve.insert(index+1,min_index)
#                    sum_distance = 0
#                    i = i+1
#
#                    #不符合，直接返回
#                    suit_distance = 0
#                    return suit_distance,serve
#        return suit_distance,serve
        
    def check_distance(self,serve):
        remain_distance = 100000
        suit_distance = 1
        new_serve = serve
        count = 0
        #for i in range(2,len(serve)-1):
        ##            sum_distance += self.distance_array[serve[i]][serve[i+1]]
        #    #求出到i点后的剩余里程数
        #   
        #    min_distance,charge_index = find_nearest(serve[i+1])
        #    #剩余里程不足以支持到下一个点以及下一个点最近的充电站，需要在本点后就去充电站
        #    if remain_distance < distance_array[serve[i]][serve[i+1]] + min_distance:
        #        min_cost = float('inf')
        #        min_index = -1
        #        for j in range(1001,1101):
        #            cost = distance_array[serve[i]][j] + distance_array[j][serve[i+1]]
        #           
        #            if cost < min_cost:
        #                min_cost = cost
        #                min_index = j
        #        if min_index != -1:
        #            #有符合时间约束的充电站可以添加
        #            new_serve.insert(i+count,min_index)
        #            print(new_serve)
        #            count+=1
        #            remain_distance = 100000 - distance_array[min_index][serve[i+1]]
        #        else:
        #            #不符合，直接返回
        #            suit_distance = 0
        #              
        #    else:
        #         remain_distance = remain_distance - distance_array[serve[i]][serve[i+1]]
        #print(new_serve)
        #print(distance_array[new_serve[2]][new_serve[3]])
        #
        #print(distance_array[new_serve[3]][new_serve[4]])
        #print(distance_array[new_serve[4]][new_serve[5]])
        
        for i in range(2,len(serve)-1):
            #不是倒数第一个客户点
            if i != len(serve)-2:
                min_distance,charge_index = self.find_nearest(serve[i+1])
                #剩余里程不足以到下一个点，需要去充电站
                if remain_distance < self.distance_array[serve[i]][serve[i+1]]:
                    _min_distance,_charge_index = self.find_nearest(serve[i])
                    #有符合约束的充电站可以添加
                    if _charge_index == -1:
                        suit_distance = 0
                        return suit_distance,new_serve
                    new_serve.insert(i+count+1,_charge_index)
                    count+=1
                    remain_distance = 100000 - self.distance_array[_charge_index][serve[i+1]]
                elif remain_distance < self.distance_array[serve[i]][serve[i+1]] + min_distance:
                    _min_distance,_charge_index = self.find_nearest(serve[i])
                    #有符合约束的充电站可以添加
                    if _charge_index == -1:
                        suit_distance = 0
                        return suit_distance,new_serve
                    new_serve.insert(i+count+1,_charge_index)
                    count+=1
                    remain_distance = 100000 - self.distance_array[_charge_index][serve[i+1]]
                else:
                    remain_distance = remain_distance - self.distance_array[serve[i]][serve[i+1]]
            #是最后一个客户点      
            else:
                if remain_distance < self.distance_array[serve[i]][0]:
                    _min_distance,_charge_index = self.find_nearest(serve[i])
                    #有符合的充电站可以添加
                    if _charge_index == -1:
                        suit_distance = 0
                        return suit_distance,new_serve
                    new_serve.insert(i+count+1,_charge_index)
                    count+=1
                    remain_distance = 100000 - self.distance_array[_charge_index][serve[i+1]]
        return suit_distance,new_serve
        
    def find_nearest(self,point_ID):
        min_distance = float('inf')
        charge_index = -1
        for i in range(1001,1101):
            if self.distance_array[point_ID][i] < min_distance:
                min_distance = self.distance_array[point_ID][i]
                charge_index = i
        return min_distance,charge_index
    
    def cal_conversation(self,origin,new):
        origin_1 = self.convert_vali(origin[0])
        origin_2 = self.convert_vali(origin[1])
        origin_cost = self.cal_cost(origin_1) + self.cal_cost(origin_2)
        check_flag,new_aval = self.convert_vali(new)
        new_cost = self.cal_cost(new_aval)
        if check_flag.count(0) != 0:
            #解不合理
            conversation = 0
        else:
            conversation = origin_cost - new_cost
        return conversation
    
    #-1：未在已构成回路中
    #0：在已构成回路中，为线路内点，不可相连
    #1：在已构成回路中，左边与车场相连
    #2：在已构成回路中，右边与车场相连  
    def cal_conversation_array(self):
        for i in range(1,1000):
            for j in range(1,1000):
                #若i的最早服务时间晚于j的最晚服务时间，节约值为0
                if self.node[i][5] > self.node[j][6]:
                    self.record_conser[i][j] = 0
                #若已经不可相连，不计算节约值，赋值为0
                if self.record_assign_array[i] == 0 or self.record_assign_array[j] == 0:
                    self.record_conser[i][j] = 0
                #均未在已构成回路中
                elif self.record_assign_array[i] == -1 and self.record_assign_array[j] == -1:
                    new_assign = [max(self.assign_list[self.record_index[i]][0],self.assign_list[self.record_index[j]][0]),min(self.assign_list[self.record_index[i]][1],self.assign_list[self.record_index[j]][1]),0,i,j,0]
                    self.record_conser[i][j] = self.cal_conversation([self.assign_list[i],self.assign_list[j]],new_assign)
                #一个未在已构成回路中，一个左边与车场相连
                elif self.record_assign_array[i] == -1 and self.record_assign_array[j] == 1:
                    new_assign = [max(self.assign_list[self.record_index[i]][0],self.assign_list[self.record_index[j]][0]),min(self.assign_list[self.record_index[i]][1],self.assign_list[self.record_index[j]][1]),0,i,j,0]
                    self.record_conser[i][j] = self.cal_conversation([self.assign_list[i],self.assign_list[j]],new_assign)
                #elif self.record_assign_array[i] == 1 and self.record_assign_array[j] == -1:   #对称的，不用考虑，之后的遍历会把这种情况考虑进去的
                #一个未在已构成回路中，一个右边与车场相连
                elif self.record_assign_array[i] == -1 and self.record_assign_array[j] == 2:
                    new_assign = [max(self.assign_list[self.record_index[i]][0],self.assign_list[self.record_index[j]][0]),min(self.assign_list[self.record_index[i]][1],self.assign_list[self.record_index[j]][1]),0,i,j,0]
                    self.record_conser[i][j] = self.cal_conversation([self.assign_list[i],self.assign_list[j]],new_assign)
                #elif self.record_assign_array[i] == 2 and self.record_assign_array[j] == -1:
                #一个左边与车场相连，一个右边与车场相连
                elif self.record_assign_array[i] == 1 and self.record_assign_array[j] == 2:
                    new_assign = [max(self.assign_list[self.record_index[i]][0],self.assign_list[self.record_index[j]][0]),min(self.assign_list[self.record_index[i]][1],self.assign_list[self.record_index[j]][1]),0,i,j,0]
                    self.record_conser[i][j] = self.cal_conversation([self.assign_list[i],self.assign_list[j]],new_assign)
                #两个均左边与车场相连
                elif self.record_assign_array[i] == 1 and self.record_assign_array[j] == 1:
                    self.record_conser[i][j] = 0
                #两个均右边与车场相连
                elif self.record_assign_array[i] == 2 and self.record_assign_array[j] == 2:
                    self.record_conser[i][j] = 0
        #在矩阵中找节约值最大的
        tup = np.where(self.record_conser == np.max(self.record_assign_array))
        from_node = tup[0][0]
        to_node = tup[1][0]
        #添加该边，同时对assign_list和record_index和record_assign_array进行修改，删除消去的支路
        if self.record_assign_array[from_node] == 0 or self.record_assign_array[j] == 0:
            self.record_conser[from_node][j] = 0
        #均未在已构成回路中
        elif self.record_assign_array[from_node] == -1 and self.record_assign_array[j] == -1:
            new_assign = [max(self.assign_list[self.record_index[from_node]][0],self.assign_list[self.record_index[j]][0]),min(self.assign_list[self.record_index[i]][1],self.assign_list[self.record_index[j]][1]),0,i,j,0]
            self.record_conser[from_node][j] = self.cal_conversation([self.assign_list[i],self.assign_list[j]],new_assign)
        #一个未在已构成回路中，一个左边与车场相连
        elif self.record_assign_array[from_node] == -1 and self.record_assign_array[j] == 1:
            new_assign = [max(self.assign_list[self.record_index[from_node]][0],self.assign_list[self.record_index[j]][0]),min(self.assign_list[self.record_index[i]][1],self.assign_list[self.record_index[j]][1]),0,i,j,0]
            self.record_conser[from_node][j] = self.cal_conversation([self.assign_list[i],self.assign_list[j]],new_assign)
        #elif self.record_assign_array[i] == 1 and self.record_assign_array[j] == -1:   #对称的，不用考虑，之后的遍历会把这种情况考虑进去的
        #一个未在已构成回路中，一个右边与车场相连
        elif self.record_assign_array[i] == -1 and self.record_assign_array[j] == 2:
            new_assign = [max(self.assign_list[self.record_index[i]][0],self.assign_list[self.record_index[j]][0]),min(self.assign_list[self.record_index[i]][1],self.assign_list[self.record_index[j]][1]),0,i,j,0]
            self.record_conser[i][j] = self.cal_conversation([self.assign_list[i],self.assign_list[j]],new_assign)
        #elif self.record_assign_array[i] == 2 and self.record_assign_array[j] == -1:
        #一个左边与车场相连，一个右边与车场相连
        elif self.record_assign_array[i] == 1 and self.record_assign_array[j] == 2:
            new_assign = [max(self.assign_list[self.record_index[i]][0],self.assign_list[self.record_index[j]][0]),min(self.assign_list[self.record_index[i]][1],self.assign_list[self.record_index[j]][1]),0,i,j,0]
            self.record_conser[i][j] = self.cal_conversation([self.assign_list[i],self.assign_list[j]],new_assign)
                    
            
    def construct_init(self,serve):
        #此函数构造初始解，首先车辆容量，再检查距离约束，再检查时间窗约束
        suit_volume,suit_weight = self.check_weight_volume(serve)
        if suit_volume == 0 or suit_weight == 0:
            serve[0] = 1
        start_time = serve[1]
        suit_distance,new_serve = self.check_distance(serve)
        suit_time_window,max_delay,require_advance_time = self.check_time_window(new_serve,0)
        while(suit_time_window == 0 and start_time-require_advance_time>time.mktime(time.strptime('1971 8:00','%Y %H:%M'))):
            suit_time_window,max_delay,require_advance_time = self.check_time_window(new_serve,require_advance_time)
            start_time -= require_advance_time
        new_serve[1] = start_time
        return suit_distance,suit_time_window,new_serve

#        for item in self.assign_list:
#            if len(item) == 6 or len(item)==7:
#                print(item)
#     
#                print(self.distance_array[item[2]][item[3]])
#                print(self.distance_array[item[3]][item[4]])
#                print(self.distance_array[item[4]][item[5]])
        
    
    def cal_cost(self,serve):
        distance = total_cost = charge_cost = trans_cost = wait_cost = static_cost = charge_time = 0
        #for serve in self.assign_list:
        current_time = serve[1]
        #车辆固定成本
        total_cost += self.vehicle[serve[0]][5]
        static_cost = self.vehicle[serve[0]][5]
        for i in range(2,len(serve)):
            #第一次从车场出发
            if i == 2:
                current_time += self.time_array[0][serve[i+1]]
            #最后一次访问0结点，仅检查硬时间窗，计算最大可延迟时间即可
            elif i == len(serve)-1:
                if current_time >self.node[serve[i]][6]:
                    break
            #除了第一次和最后一次访问起点，要加上等待时间以及到下一个点的时间
            elif serve[i] == 0 and (i != 2 and i != len(serve)-1):
                total_cost += 24   
                wait_cost += 24
                if current_time > self.node[serve[i]][6]:
                    break
                else:
#                    print(time.strftime('%H:%M',time.localtime(current_time)))
                    current_time += 60*60
                    current_time += self.time_array[0][serve[i+1]]
#                    print(time.strftime('%H:%M',time.localtime(current_time)))
            #充电站，充电0.5小时
            elif serve[i] in range(1001,1101):
                total_cost += 50
                charge_cost += 50
                charge_time += 1
#                print(time.strftime('%H:%M',time.localtime(current_time)))
                current_time += 0.5*60*60
                current_time += self.time_array[serve[i]][serve[i+1]]
#                print(time.strftime('%H:%M',time.localtime(current_time)))
            #访问商家，卸货，如果早于最早，还要等到最早服务时间
            elif serve[i] in range(1,1001):
                if current_time < self.node[serve[i]][5]:
                    total_cost += (self.node[serve[i]][5] - current_time)*24/3600
                    wait_cost += (self.node[serve[i]][5] - current_time)*24/3600
#                    print(time.strftime('%H:%M',time.localtime(current_time)))
                    current_time =self.node[serve[i]][5]
                    current_time += 0.5*60*60
                    current_time += self.time_array[serve[i]][serve[i+1]]
#                    print(time.strftime('%H:%M',time.localtime(current_time)))
                elif current_time >self.node[serve[i]][6]:
                    break
                else:
#                    print(time.strftime('%H:%M',time.localtime(current_time)))
                    current_time += 0.5*60*60
                    current_time += self.time_array[serve[i]][serve[i+1]]
#                    print(time.strftime('%H:%M',time.localtime(current_time)))
            if i != len(serve)-1:
                total_cost += self.distance_array[serve[i]][serve[i+1]]*self.vehicle[serve[0]][4]/1000
                trans_cost += self.distance_array[serve[i]][serve[i+1]]*self.vehicle[serve[0]][4]/1000
                distance += self.distance_array[serve[i]][serve[i+1]]  
        return total_cost,current_time,distance,trans_cost,charge_cost,wait_cost,static_cost,charge_time
    
    def write_csv(self):
        result = open('..\..\Result.csv','w',newline = '')
        csv_write = csv.writer(result)
        csv_write.writerow(["trans_code    ","vehicle_type    ","dist_seq","distribute_lea_tm","distribute_arr_tm","distance","trans_cost","charge_cost","wait_cost","fixed_use_cost","total_cost","charge_cnt"])
        for i in range(len(self.assign_list)):
            assign_str = ''
            for j in range(2,len(self.assign_list[i])-1):
                assign_str = assign_str + '%d'%(self.assign_list[i][j]) +';'
            assign_str = assign_str + '0'
            total_cost,current_time,distance,trans_cost,charge_cost,wait_cost,static_cost,charge_time = self.cal_cost(self.assign_list[i])
            result_string = ['DP%04d'%(i+1),'%d'%(self.assign_list[i][0]+1),assign_str,time.strftime('%H:%M',time.localtime(self.assign_list[i][1])), time.strftime('%H:%M',time.localtime(current_time)),\
                            '%d'%(distance) , '%.2f'%(trans_cost) , '%d'%(charge_cost) , '%.2f'%(wait_cost) , '%d'%(static_cost) , '%.2f'%(total_cost) , '%d'%(charge_time)]
            if i==0:
                print(result_string)
            csv_write.writerow(result_string)
    
if __name__ == '__main__':
    a = solution()
    a.write_csv()