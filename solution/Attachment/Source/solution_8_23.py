# -*- coding: utf-8 -*-
"""
Created on Sun Jun 24 10:51:00 2018

@author: bittdy
"""
import csv
import numpy as np
import time
import datetime
import copy
#import os

class solution(object):
    def __init__(self,id):   
        #读取相关数据
        #时间统一为秒，距离统一为米
        #file_path = os.getcwd()
        self.assign_list = []
        self.assign_list_final = []
        self.new_assign_list = []
        
        self.data = {1:1601,2:1501,3:1401,4:1301,5:1201}
        self.charge_begin_index = {1:1501,2:1401,3:1301,4:1201,5:1101}
        self.id = id
        
        self.distance_array = np.zeros((self.data[self.id],self.data[self.id]))
        self.time_array = np.zeros((self.data[self.id],self.data[self.id]))
        with open('..\..\..\inputdistancetime_'+str(self.id)+'_'+str(self.data[self.id])+'.csv','r') as distance_time:
            r = csv.DictReader(distance_time)
            for line in r:
                self.distance_array[int(line['from_node'])%10000][int(line['to_node'])%10000] = line['distance']
                self.time_array[int(line['from_node'])%10000][int(line['to_node'])%10000] = int(line['spend_tm'])*60
#        print(self.distance_array[5][6],self.time_array[7][8])
        
        self.node = np.zeros((self.data[self.id],7))
        with open('..\..\..\inputnode_'+str(self.id)+'_'+str(self.data[self.id])+'.csv','r') as input_node:
            r = csv.DictReader(input_node)
            for line in r:
                self.node[int(line['ID'])%10000][0] = line['type']
                self.node[int(line['ID'])%10000][1] = line['lng                 ']
                self.node[int(line['ID'])%10000][2] = line['lat                 ']
                if line['type'] == '1':  #起点
#                    print(line['first_receive_tm'])
#                    print(line['last_receive_tm'])
                    self.node[int(line['ID'])%10000][3] = 0
                    self.node[int(line['ID'])%10000][4] = 0
                    self.node[int(line['ID'])%10000][5] = time.mktime(time.strptime('1971 '+line['first_receive_tm'],'%Y %H:%M'))
                    self.node[int(line['ID'])%10000][6] = time.mktime(time.strptime('1971 '+'23:59','%Y %H:%M')) + 60
                elif line['type'] == '2' or line['type'] == '3':#商家
                    self.node[int(line['ID'])%10000][3] = line['pack_total_weight']
                    self.node[int(line['ID'])%10000][4] = line['pack_total_volume']
                    self.node[int(line['ID'])%10000][5] = time.mktime(time.strptime('1971 '+line['first_receive_tm'],'%Y %H:%M'))
                    first_time = self.node[int(line['ID'])%10000][5]
                    self.node[int(line['ID'])%10000][6] = time.mktime(time.strptime('1971 '+line['last_receive_tm'],'%Y %H:%M'))
                    #加一步判断，如果1号车不能满足初始派2号车
                    if first_time-self.time_array[0][int(line['ID'])%10000]<time.mktime(time.strptime('1971 8:00','%Y %H:%M')):
                        self.assign_list.append([0,time.mktime(time.strptime('1971 8:00','%Y %H:%M')),0,int(line['ID'])%10000,0])#若出发时间早于8点，则定为8点
                    else:
                        self.assign_list.append([0,first_time-self.time_array[0][int(line['ID'])%10000],0,int(line['ID'])%10000,0])  #出发时间定为最晚的不让每个客户等待的时间
                elif line['type'] == '4':#充电站
                    self.node[int(line['ID'])%10000][3] = 0
                    self.node[int(line['ID'])%10000][4] = 0
                    self.node[int(line['ID'])%10000][5] = 0
                    self.node[int(line['ID'])%10000][6] = 0
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
#        print(self.vehicle[1][4])
        #p = self.cal_cost([1,31550000.0,2,0])
        #print(p)
        #构造解时，先找距离约束，再算时间约束
#        for p in range(len(self.assign_list)):
#            distance_flag,time_window_flag,new_serve = self.construct_init(self.assign_list[p])
#            self.assign_list[p] = new_serve
#            if distance_flag == 0 or time_window_flag == 0:
#                print('origin:',self.assign_list[p])
#                print('distance_flag:',distance_flag)
#                print('time_window_flag:',time_window_flag)
#                print('new_serve:',new_serve)        

              
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
#                    print('i:',i)
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
            elif self.node[serve[i]][0] == 4:
                current_time += 0.5*60*60
                current_time += self.time_array[serve[i]][serve[i+1]]
                require_advance_time = 0
            #访问商家，卸货，如果早于最早，还要等到最早服务时间
            elif self.node[serve[i]][0] == 2 or self.node[serve[i]][0] == 3:
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
#                    print('i:',i)
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
#        suit_capacity = 1
        volume = weight = 0
        for i in range(2,len(serve)):
            if self.node[serve[i]][0] == 2:
                weight += self.node[serve[i]][3]
                volume += self.node[serve[i]][4]
        if weight > self.vehicle[serve[0]][1] or volume > self.vehicle[serve[0]][0]:
            return 0
        #计算车辆出发时剩余的体积与重量
        remain_weight = self.vehicle[serve[0]][1] - weight
        remain_volume = self.vehicle[serve[0]][0] - volume
        #记录揽收的货物体积与重量，遇0清空
        collect_weight = 0
        collect_volume = 0
        for i in range(2,len(serve)):
            if self.node[serve[i]][0] == 2:
                remain_weight += self.node[serve[i]][3]
                remain_volume += self.node[serve[i]][4]
            elif self.node[serve[i]][0] == 3:
                if remain_weight < self.node[serve[i]][3] or remain_volume < self.node[serve[i]][4]:
                    #剩余重量与体积空间不足以揽收
                    return 0
                else:
                    remain_weight -= self.node[serve[i]][3]
                    remain_volume -= self.node[serve[i]][4]
                    collect_weight += self.node[serve[i]][3]
                    collect_volume += self.node[serve[i]][4]
            elif i == 0:
                #清空揽收货物
                remain_weight += collect_weight
                remain_volume += collect_volume
                collect_weight = 0
                collect_volume = 0
        return 1
    
       #jiaru 0 
    def check_distance(self,serve):
        remain_distance = self.vehicle[serve[0]][2]
        suit_distance = 1
        new_serve = copy.deepcopy(serve)
        count = 0
        for i in range(2,len(serve)-1):
            #不是倒数第一个客户点
            if i != len(serve)-2:
                min_distance,charge_index = self.find_nearest_charge(serve[i+1],self.vehicle[serve[0]][4])
                #剩余里程不足以到下一个点，需要去充电站
                if remain_distance < self.distance_array[serve[i]][serve[i+1]]:
                    _min_distance,_charge_index = self.find_nearest_charge(serve[i],self.vehicle[serve[0]][4])
                    #有符合约束的充电站可以添加
                    if _charge_index == -1:
                        suit_distance = 0
                        return suit_distance,new_serve
                    new_serve.insert(i+count+1,_charge_index)
                    count+=1
                    remain_distance = self.vehicle[serve[0]][2] - self.distance_array[_charge_index][serve[i+1]]
                    #print(self.distance_array[_charge_index][serve[i+1]],remain_distance)
                elif remain_distance < self.distance_array[serve[i]][serve[i+1]] + min_distance:
                    _min_distance,_charge_index = self.find_nearest_charge(serve[i],self.vehicle[serve[0]][4])
                    #有符合约束的充电站可以添加
                    if _charge_index == -1:
                        suit_distance = 0
                        return suit_distance,new_serve
                    new_serve.insert(i+count+1,_charge_index)
                    count+=1
                    remain_distance = self.vehicle[serve[0]][2] - self.distance_array[_charge_index][serve[i+1]]
                    #print(self.distance_array[_charge_index][serve[i+1]],remain_distance)
                else:
                    remain_distance = remain_distance - self.distance_array[serve[i]][serve[i+1]]
                    #print(self.distance_array[serve[i]][serve[i+1]],remain_distance)
            #是最后一个客户点      
            else:
                #print(remain_distance,self.distance_array[serve[i]][0])
                if remain_distance < self.distance_array[serve[i]][0]:
                    _min_distance,_charge_index = self.find_nearest_charge(serve[i],self.vehicle[serve[0]][4])
                    #有符合的充电站可以添加
                    if _charge_index == -1:
                        suit_distance = 0
                        return suit_distance,new_serve
                    new_serve.insert(i+count+1,_charge_index)
                    count+=1
                    remain_distance = self.vehicle[serve[0]][2] - self.distance_array[_charge_index][serve[i+1]]
                    #print(self.distance_array[_charge_index][serve[i+1]],remain_distance)
        return suit_distance,new_serve
    
    def find_nearest_charge(self,point_ID,unit_cost):
        #加入0
        min_distance = float('inf')
        charge_index = -1
        for i in range(self.charge_begin_index[self.id],self.data[self.id]):
            if self.distance_array[point_ID][i] < min_distance:
                min_distance = self.distance_array[point_ID][i]
                charge_index = i
        charge_cost = unit_cost * min_distance + 50
        back_cost = self.distance_array[point_ID][0] * unit_cost + 24
        if back_cost < charge_cost:
            #若回配送中心的花费更小
            min_distance = self.distance_array[point_ID][0]
            charge_index = 0
        return min_distance,charge_index
    
    def find_nearest_custom_in_list(self,point_ID,search_list):
        min_distance = float('inf')
        charge_index = -1
        for i in range(len(search_list)):
            if self.distance_array[point_ID][search_list[i]] < min_distance:
                min_distance = self.distance_array[point_ID][search_list[i]]
                charge_index = search_list[i]
        return min_distance,charge_index
    
    def find_farthest_custom_in_list(self,point_ID,search_list):
        max_distance = 0
        charge_index = -1
        for i in range(len(search_list)):
            if self.distance_array[point_ID][search_list[i]] > max_distance:
                max_distance = self.distance_array[point_ID][search_list[i]]
                charge_index = search_list[i]
        return max_distance,charge_index
    
    def find_nearest_quantity_custom_in_list(self,quantity,point_ID,search_list):
        min_distance_list = [float('inf')]*quantity
        charge_index_list = [-1]*quantity    
        for i in range(len(search_list)):
            if self.distance_array[point_ID][search_list[i]] < max(min_distance_list):
                min_distance_list[min_distance_list.index(max(min_distance_list))] = self.distance_array[point_ID][search_list[i]]
                charge_index_list[min_distance_list.index(max(min_distance_list))] = search_list[i]
        return min_distance_list,charge_index_list
    
    def find_nearest_quantity_custom_in_list_by_tw(self,quantity,point_ID,search_list):
        min_dtime_list = [float('inf')]*quantity
        custom_index_list = [-1]*quantity    
        for i in range(len(search_list)):
            if abs(self.node[point_ID][6] - self.node[search_list[i]][6]) < max(min_dtime_list):
                min_dtime_list[min_dtime_list.index(max(min_dtime_list))] = abs(self.node[point_ID][6] - self.node[search_list[i]][6])
                custom_index_list[min_dtime_list.index(max(min_dtime_list))] = search_list[i]
        return min_dtime_list,custom_index_list
    
    def find_nearest_quantity_custom_in_list_by_weight(self,quantity,point_ID,search_list):
        min_distance_time_list = [float('inf')]*quantity
        custom_index_list = [-1]*quantity    
        for i in range(len(search_list)):
            if (0.005*(self.node[point_ID][6] - self.node[search_list[i]][6]))**2 + self.distance_array[point_ID][search_list[i]]**2 - (0.35*self.distance_array[0][search_list[i]])**2< max(min_distance_time_list):
                min_distance_time_list[min_distance_time_list.index(max(min_distance_time_list))] = (0.01*(self.node[point_ID][6] - self.node[search_list[i]][6]))**2 + self.distance_array[point_ID][search_list[i]]**2 
                custom_index_list[min_distance_time_list.index(max(min_distance_time_list))] = search_list[i]
        return min_distance_time_list,custom_index_list
    
    def find_farthest_quantity_custom_in_list(self,quantity,point_ID,search_list):
        max_distance_list = [0]*quantity
        charge_index_list = [-1]*quantity    
        for i in range(len(search_list)):
            if self.distance_array[point_ID][search_list[i]] > min(max_distance_list) and self.distance_array[point_ID][search_list[i]] < 50000:
                max_distance_list[max_distance_list.index(min(max_distance_list))] = self.distance_array[point_ID][search_list[i]]
                charge_index_list[max_distance_list.index(min(max_distance_list))] = search_list[i]
        return max_distance_list,charge_index_list
    
    def find_nearest_custom(self,point_ID):
        min_distance = float('inf')
        custom_index = -1
        for i in range(1,self.charge_begin_index[self.id]):
            if i == point_ID:
                continue
            if self.distance_array[point_ID][i] < min_distance:
                min_distance = self.distance_array[point_ID][i]
                custom_index = i
        return min_distance,custom_index
    
    def find_farthest_custom(self,point_ID):
        max_distance = 0
        custom_index = -1
        for i in range(1,self.charge_begin_index[self.id]):
            if i == point_ID:
                continue
            if self.distance_array[point_ID][i] > max_distance:
                max_distance = self.distance_array[point_ID][i]
                custom_index = i
        return max_distance,custom_index
    
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
    #最近邻插入
    def insert(self):
        has_inserted = []
        not_inserted = [n for n in range(1,self.charge_begin_index[self.id])]
        #当仍有顾客点未被服务
        while(len(not_inserted) != 0):
            #在未分配点中找与车场最近的点作为起始点，构成初始解，计算花费
            distance,index = self.find_nearest_custom_in_list(0,not_inserted)
            has_inserted.append(index)
            not_inserted.remove(index)
            init_serve = self.assign_list[index-1]
            #循环遍历未插入点，找使花费值增长最小的出入点以及插入位置，同时检查解的可行性
            test_serve = copy.deepcopy(init_serve)
            if len(not_inserted) == 0:
                #把最后一个没进入while的客户点也构造解加入到assign中
                suit_capacity,suit_distance,suit_time_window,new_serve = self.construct_avai(test_serve)
                self.assign_list_final.append(new_serve)
            while(len(not_inserted) != 0):
                min_inc_cost = float('inf')
                min_inc_ins_pos = -1
                min_inc_cus_ind = -1
                buff_serve = copy.deepcopy(test_serve)
                for ins_pos in range(3,len(test_serve)):
                    if len(not_inserted) > 35:
                        min_distance_list,cus_ind_list = self.find_nearest_quantity_custom_in_list_by_weight(35,buff_serve[ins_pos-1],not_inserted)
                    #min_distance,cus_ind = self.find_nearest_custom_in_list(buff_serve[ins_pos-1],not_inserted)
                    else:
                        cus_ind_list = copy.deepcopy(not_inserted)
                    for cus_ind in cus_ind_list:   
                    #for cus_ind in not_inserted:
                    #找一个buffer，保持原列表不变
                        buff_serve = copy.deepcopy(test_serve)
                        buff_serve.insert(ins_pos,cus_ind)
                        suit_capacity,suit_distance,suit_time_window,new_serve = self.construct_avai(buff_serve)
                        if suit_distance & suit_time_window & suit_capacity== 0:
                            continue
                        else:
                            total_cost,current_time,distance,trans_cost,charge_cost,wait_cost,static_cost,charge_time = self.cal_cost(new_serve)
                            ori_total_cost,ori_current_time,ori_distance,ori_trans_cost,ori_charge_cost,ori_wait_cost,ori_static_cost,ori_charge_time = self.cal_cost(test_serve)
                            inc_cost = total_cost - ori_total_cost
                            if inc_cost < min_inc_cost:
                                min_inc_cost = inc_cost
                                min_inc_cus_ind = cus_ind
                                min_inc_ins_pos = ins_pos
                #若未找到，将当前解加入到assign_list中去，并跳出本while
                if min_inc_cus_ind == -1:
                    suit_capacity,suit_distance,suit_time_window,new_serve = self.construct_avai(test_serve)
                    self.assign_list_final.append(new_serve)
                    print(test_serve)
                    print(len(not_inserted))
                    break
                #若找到了，构造新的解，加入到结果中，并在not inserted中删掉
                else:
                    test_serve.insert(min_inc_ins_pos,min_inc_cus_ind)
                    has_inserted.append(min_inc_cus_ind)
                    not_inserted.remove(min_inc_cus_ind)
            #find nearest里面要加上0，代价加上等待代价
            #也要把0加入到待插入列表中，但是插入后不能删除
        #保证无客户点被遗漏，之后查代码bug
        all = [n for n in range(1,self.charge_begin_index[self.id])]
        for assign in self.assign_list_final:
            for item in assign[3:]:
                if item == 0:
                    continue
                else:
                    if item >= self.charge_begin_index[self.id]:
                        continue
                    all.remove(item) 
        for not_assign in all:
            serve = self.assign_list[not_assign - 1]
            suit_capacity,suit_distance,suit_time_window,new_serve = self.construct_avai(serve)
            self.assign_list_final.append(new_serve)
            
    #小规模最近邻插入
    def little_insert(self,serve_1,serve_2):
        new_total_cost = 0
        has_inserted = []
        if len(serve_1) > len(serve_2):
            not_inserted = self.unpack_single(serve_2)
            test_serve = copy.deepcopy(serve_1)
        else:
            not_inserted = self.unpack_single(serve_1)
            test_serve = copy.deepcopy(serve_2)
        new_assign = []
        #当仍有顾客点未被服务
        while(len(not_inserted) != 0):
            #在未分配点中找与车场最近的点作为起始点，构成初始解，计算花费
            distance,index = self.find_nearest_custom_in_list(0,not_inserted)
            has_inserted.append(index)
            not_inserted.remove(index)
            init_serve = self.assign_list[index-1]
            #循环遍历未插入点，找使花费值增长最小的出入点以及插入位置，同时检查解的可行性
            test_serve = copy.deepcopy(init_serve)
            if len(not_inserted) == 0:
                #把最后一个没进入while的客户点也构造解加入到assign中
                suit_capacity,suit_distance,suit_time_window,new_serve = self.construct_avai(test_serve)
                new_assign.append(new_serve)
            while(len(not_inserted) != 0):
                min_inc_cost = float('inf')
                min_inc_ins_pos = -1
                min_inc_cus_ind = -1
                buff_serve = copy.deepcopy(test_serve)
                for ins_pos in range(3,len(test_serve)):
                    for cus_ind in not_inserted:
                    #找一个buffer，保持原列表不变
                        buff_serve = copy.deepcopy(test_serve)
                        buff_serve.insert(ins_pos,cus_ind)
                        suit_capacity,suit_distance,suit_time_window,new_serve = self.construct_avai(buff_serve)
                        if suit_distance & suit_time_window & suit_capacity== 0:
                            continue
                        else:
                            total_cost,current_time,distance,trans_cost,charge_cost,wait_cost,static_cost,charge_time = self.cal_cost(new_serve)
                            ori_total_cost,ori_current_time,ori_distance,ori_trans_cost,ori_charge_cost,ori_wait_cost,ori_static_cost,ori_charge_time = self.cal_cost(test_serve)
                            inc_cost = total_cost - ori_total_cost
                            if inc_cost < min_inc_cost:
                                min_inc_cost = inc_cost
                                min_inc_cus_ind = cus_ind
                                min_inc_ins_pos = ins_pos
                #若未找到，将当前解加入到assign_list中去，并跳出本while
                if min_inc_cus_ind == -1:
                    suit_capacity,suit_distance,suit_time_window,new_serve = self.construct_avai(test_serve)
                    new_assign.append(new_serve)
#                    print(test_serve)
#                    print(len(not_inserted))
                    break
                #若找到了，构造新的解，加入到结果中，并在not inserted中删掉
                else:
                    test_serve.insert(min_inc_ins_pos,min_inc_cus_ind)
                    has_inserted.append(min_inc_cus_ind)
                    not_inserted.remove(min_inc_cus_ind)
            #find nearest里面要加上0，代价加上等待代价
            #也要把0加入到待插入列表中，但是插入后不能删除
        #保证无客户点被遗漏，之后查代码bug
        all = copy.deepcopy(points_list)
        for assign in new_assign:
            for item in assign[3:]:
                if item == 0:
                    continue
                else:
                    if item >= self.charge_begin_index[self.id]:
                        continue
                    all.remove(item) 
        for not_assign in all:
            serve = self.assign_list[not_assign - 1]
            suit_capacity,suit_distance,suit_time_window,new_serve = self.construct_avai(serve)
            new_assign.append(new_serve)
        for assign in new_assign:
            total_cost,current_time,distance,trans_cost,charge_cost,wait_cost,static_cost,charge_time = self.cal_cost(assign)
            new_total_cost += total_cost
        return new_total_cost,new_assign
            
    def construct_avai(self,serve):
        #此函数构造可行解，首先车辆容量，再检查距离约束，再检查时间窗约束
        suit_capacity = self.check_weight_volume(serve)
        if suit_capacity == 0 and serve[0] == 0:
            serve[0] = 1
            suit_capacity = self.check_weight_volume(serve)            
        start_time = serve[1]
        suit_distance,new_serve = self.check_distance(serve)
        suit_time_window,max_delay,require_advance_time = self.check_time_window(new_serve,0)
        while(suit_time_window == 0 and start_time-require_advance_time>time.mktime(time.strptime('1971 8:00','%Y %H:%M'))):
            suit_time_window,max_delay,require_advance_time = self.check_time_window(new_serve,require_advance_time)
            start_time -= require_advance_time
        new_serve[1] = start_time
        return suit_capacity,suit_distance,suit_time_window,new_serve
    
    def unpack(self,points_list_1,points_list_2):
        points_list = []
        for i in range(3,len(points_list_1)):
            if points_list_1[i] == 0 or points_list_1[i] >= self.charge_begin_index[self.id]:
                continue
            points_list.append(points_list_1[i])
        for j in range(3,len(points_list_2)):
            if points_list_2[j] == 0 or points_list_2[j] >= self.charge_begin_index[self.id]:
                continue
            points_list.append(points_list_2[j])
        return points_list
    
    def unpack_single(self,serve):
        points_list = []
        for i in range(3,len(serve)):
            if serve[i] == 0 or serve[i] >= self.charge_begin_index[self.id]:
                continue
            points_list.append(serve[i])
        return points_list
    
    def c_w_combination(self):
        max_c_w = 0
        max_i_j = [0,0]
        max_new_assign = []
        assign_1_buffer = []
        assign_2_buffer = []
        for i in range(0,len(self.assign_list_final)):
            assign_1 = copy.deepcopy(self.assign_list_final[i])
            for j in range(0,len(self.assign_list_final)):
                print(j)
                if j == i:
                    continue
                assign_2 = copy.deepcopy(self.assign_list_final[j])
                total_cost_1,current_time_1,distance_1,trans_cost_1,charge_cost_1,wait_cost_1,static_cost_1,charge_time_1 = self.cal_cost(assign_1)
                total_cost_2,current_time_2,distance_2,trans_cost_2,charge_cost_2,wait_cost_2,static_cost_2,charge_time_2 = self.cal_cost(assign_2)
                origin_total_cost = total_cost_1 + total_cost_2
                points_list = self.unpack(assign_1,assign_2)
                new_total_cost,new_assign = self.little_insert(points_list)
                c_w = origin_total_cost - new_total_cost
                if c_w > max_c_w:
                    max_c_w = c_w
                    max_i_j[0] = i
                    max_i_j[1] = j
                    max_new_assign = copy.deepcopy(new_assign)
                    assign_1_buffer = copy.deepcopy(assign_1)
                    assign_2_buffer = copy.deepcopy(assign_2)
                if max_c_w > 300:
                    break
            if max_c_w > 300:
                break
        self.assign_list_final.remove(assign_1_buffer)
        self.assign_list_final.remove(assign_2_buffer)
        for assign in max_new_assign:
            self.assign_list_final.append(assign)                    
        print("reduce ",max_c_w," this time")
    
    def insert_sec(self):
        find_ins = 0
        not_inserted = []
        not_inserted_buffer = copy.deepcopy(not_inserted)
        for item in self.assign_list_final:
            if len(item) > 6:
                self.new_assign_list.append(item)
            else:
                points_list = self.unpack_single(item)
                if len(points_list) > 1:
                    self.new_assign_list.append(item)
                else:
                    not_inserted.append(points_list[0])
        not_inserted_buffer = copy.deepcopy(not_inserted)
        for item in not_inserted_buffer:
            for i in range(0,len(self.new_assign_list)):
                assign_buffer = copy.deepcopy(self.new_assign_list[i])
                for ins_pos in range(3,len(assign_buffer)):
                    buff_serve = copy.deepcopy(assign_buffer)
                    buff_serve.insert(ins_pos,item)
                    suit_capacity,suit_distance,suit_time_window,new_serve = self.construct_avai(buff_serve)
                    if suit_distance & suit_time_window & suit_capacity== 0:
                        continue
                    else:
                        self.new_assign_list[i] = copy.deepcopy(new_serve)
                        print('insert:',new_serve)
                        not_inserted.remove(item)
                        find_ins = 1
                        break
                if find_ins == 1:
                    find_ins = 0
                    break
            #若未找到，item保留在not_inserted中
         #最后，对于仍在not_inserted中的点在进行一次insert
        while(len(not_inserted) != 0):
            #在未分配点中找与车场最近的点作为起始点，构成初始解，计算花费
            distance,index = self.find_nearest_custom_in_list(0,not_inserted)
            not_inserted.remove(index)
            init_serve = self.assign_list[index-1]
            #循环遍历未插入点，找使花费值增长最小的出入点以及插入位置，同时检查解的可行性
            test_serve = copy.deepcopy(init_serve)
            if len(not_inserted) == 0:
                #把最后一个没进入while的客户点也构造解加入到assign中
                suit_capacity,suit_distance,suit_time_window,new_serve = self.construct_avai(test_serve)
                self.new_assign_list.append(new_serve)
            while(len(not_inserted) != 0):
                min_inc_cost = float('inf')
                min_inc_ins_pos = -1
                min_inc_cus_ind = -1
                buff_serve = copy.deepcopy(test_serve)
                for ins_pos in range(3,len(test_serve)):
                    if len(not_inserted) > 35:
                        min_distance_list,cus_ind_list = self.find_nearest_quantity_custom_in_list_by_weight(35,buff_serve[ins_pos-1],not_inserted)
                    #min_distance,cus_ind = self.find_nearest_custom_in_list(buff_serve[ins_pos-1],not_inserted)
                    else:
                        cus_ind_list = copy.deepcopy(not_inserted)
                    for cus_ind in cus_ind_list:   
                    #for cus_ind in not_inserted:
                    #找一个buffer，保持原列表不变
                        buff_serve = copy.deepcopy(test_serve)
                        buff_serve.insert(ins_pos,cus_ind)
                        suit_capacity,suit_distance,suit_time_window,new_serve = self.construct_avai(buff_serve)
                        if suit_distance & suit_time_window & suit_capacity== 0:
                            continue
                        else:
                            total_cost,current_time,distance,trans_cost,charge_cost,wait_cost,static_cost,charge_time = self.cal_cost(new_serve)
                            ori_total_cost,ori_current_time,ori_distance,ori_trans_cost,ori_charge_cost,ori_wait_cost,ori_static_cost,ori_charge_time = self.cal_cost(test_serve)
                            inc_cost = total_cost - ori_total_cost
                            if inc_cost < min_inc_cost:
                                min_inc_cost = inc_cost
                                min_inc_cus_ind = cus_ind
                                min_inc_ins_pos = ins_pos
                #若未找到，将当前解加入到assign_list中去，并跳出本while
                if min_inc_cus_ind == -1:
                    suit_capacity,suit_distance,suit_time_window,new_serve = self.construct_avai(test_serve)
                    self.new_assign_list.append(new_serve)
                    #print(test_serve)
                    #print(len(not_inserted))
                    break
                #若找到了，构造新的解，加入到结果中，并在not inserted中删掉
                else:
                    test_serve.insert(min_inc_ins_pos,min_inc_cus_ind)
                    not_inserted.remove(min_inc_cus_ind)
            #find nearest里面要加上0，代价加上等待代价
            #也要把0加入到待插入列表中，但是插入后不能删除
        #保证无客户点被遗漏，之后查代码bug
        all = [n for n in range(1,self.charge_begin_index[self.id])]
        for assign in self.assign_list_final:
            for item in assign[3:]:
                if item == 0:
                    continue
                else:
                    if item >= self.charge_begin_index[self.id]:
                        continue
                    all.remove(item) 
        for not_assign in all:
            serve = self.assign_list[not_assign - 1]
            suit_capacity,suit_distance,suit_time_window,new_serve = self.construct_avai(serve)
            self.new_assign_list.append(new_serve)
            
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
            elif serve[i] in range(self.charge_begin_index[self.id],self.data[self.id]):
                total_cost += 50
                charge_cost += 50
                charge_time += 1
#                print(time.strftime('%H:%M',time.localtime(current_time)))
                current_time += 0.5*60*60
                current_time += self.time_array[serve[i]][serve[i+1]]
#                print(time.strftime('%H:%M',time.localtime(current_time)))
            #访问商家，卸货，如果早于最早，还要等到最早服务时间
            elif serve[i] in range(1,self.charge_begin_index[self.id]):
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
    
    def write_csv(self,stime):
        result = open('..\..\Result_'+ str(self.id) + '_' + '%.1f'%(stime) + '.csv','w',newline = '')
        csv_write = csv.writer(result)
        csv_write.writerow(["trans_code    ","vehicle_type    ","dist_seq","distribute_lea_tm","distribute_arr_tm","distance","trans_cost","charge_cost","wait_cost","fixed_use_cost","total_cost","charge_cnt"])
        for i in range(len(self.assign_list_final)):
            assign_str = '0;'
            for j in range(3,len(self.assign_list_final[i])-1):
                assign_str = assign_str + str(self.id) + '%04d'%(self.assign_list_final[i][j]) +';'
            assign_str = assign_str + '0'
            total_cost,current_time,distance,trans_cost,charge_cost,wait_cost,static_cost,charge_time = self.cal_cost(self.assign_list_final[i])
            result_string = ['DP%04d'%(i+1),'%d'%(self.assign_list_final[i][0]+1),assign_str,time.strftime('%H:%M',time.localtime(self.assign_list_final[i][1])), time.strftime('%H:%M',time.localtime(current_time)),\
                            '%d'%(distance) , '%.2f'%(trans_cost) , '%d'%(charge_cost) , '%.2f'%(wait_cost) , '%d'%(static_cost) , '%.2f'%(total_cost) , '%d'%(charge_time)]
            if i==0:
                print(result_string)
            csv_write.writerow(result_string)
    
if __name__ == '__main__':
    for i in range(1,6):
        print("start",datetime.datetime.now())
        begin_time = time.time()
        a = solution(i)
    #    test = [1, 31538340.0, 0, 775, 424, 421, 192, 935, 708, 371, 0]
        print("load data finish and begin construct answer",datetime.datetime.now())
        a.insert()
        print("the first time insert has finished and now begin the second time")
        a.insert_sec()
    #    suit_volume,suit_weight,suit_distance,suit_time_window,new_serve = a.construct_avai(test)
        print("finish",datetime.datetime.now())
#        for i in range(0,100):
#            print("this is ",i," th c_w")
#            a.c_w_combination()
            
        end_time = time.time()
        a.write_csv(end_time - begin_time)
#    test = [0, 31536000.0, 0, 473, 317, 204, 231, 708, 347, 1383, 1320, 1304, 1302, 1462, 0]
#    a = solution(1)
#    suit_distance,new_serve = a.check_distance(test)