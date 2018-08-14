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
    def __init__(self):   
        test = [1, 31538340.0, 0, 775, 424, 421, 192, 935, 1074, 1074, 708, 371, 0]
        #读取相关数据
        #时间统一为秒，距离统一为米
        #file_path = os.getcwd()
        self.assign_list = []
        self.assign_list_final = []
        #维护两个一维数组，一个记录每个点在哪个列表里，为-1则没分配，另一个记录该点在哪个assign_list中
        record_list = [-1]*1000
        record_ind = [n for n in range(1000)]
        self.record_assign_array = np.array(record_list)
        self.record_index = np.array(record_ind)
        #维护一个二维数组，记录节约值
        self.record_conser = np.zeros((1001,1001))
        
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
    
        
    def check_distance(self,serve):
        remain_distance = 100000
        suit_distance = 1
        new_serve = serve
        count = 0
        
        for i in range(2,len(serve)-1):
            #不是倒数第一个客户点
            if i != len(serve)-2:
                min_distance,charge_index = self.find_nearest_charge(serve[i+1])
                #剩余里程不足以到下一个点，需要去充电站
                if remain_distance < self.distance_array[serve[i]][serve[i+1]]:
                    _min_distance,_charge_index = self.find_nearest_charge(serve[i])
                    #有符合约束的充电站可以添加
                    if _charge_index == -1:
                        suit_distance = 0
                        return suit_distance,new_serve
                    new_serve.insert(i+count+1,_charge_index)
                    count+=1
                    remain_distance = 100000 - self.distance_array[_charge_index][serve[i+1]]
                elif remain_distance < self.distance_array[serve[i]][serve[i+1]] + min_distance:
                    _min_distance,_charge_index = self.find_nearest_charge(serve[i])
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
                    _min_distance,_charge_index = self.find_nearest_charge(serve[i])
                    #有符合的充电站可以添加
                    if _charge_index == -1:
                        suit_distance = 0
                        return suit_distance,new_serve
                    new_serve.insert(i+count+1,_charge_index)
                    count+=1
                    remain_distance = 100000 - self.distance_array[_charge_index][serve[i+1]]
        return suit_distance,new_serve
        
    def find_nearest_charge(self,point_ID):
        min_distance = float('inf')
        charge_index = -1
        for i in range(1001,1101):
            if self.distance_array[point_ID][i] < min_distance:
                min_distance = self.distance_array[point_ID][i]
                charge_index = i
        return min_distance,charge_index
    
    def find_nearest_custom_in_list(self,point_ID,search_list):
        min_distance = float('inf')
        charge_index = -1
        for i in range(len(search_list)):
            if self.distance_array[point_ID][search_list[i]] < min_distance:
                min_distance = self.distance_array[point_ID][search_list[i]]
                charge_index = search_list[i]
        return min_distance,charge_index
    
    def find_nearest_custom(self,point_ID):
        min_distance = float('inf')
        custom_index = -1
        for i in range(1,1001):
            if i == point_ID:
                continue
            if self.distance_array[point_ID][i] < min_distance:
                min_distance = self.distance_array[point_ID][i]
                custom_index = i
        return min_distance,custom_index
    
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
    
    def insert(self):
        has_inserted = []
        not_inserted = [n for n in range(1,1001)]
        #当仍有顾客点未被服务
        while(len(not_inserted) != 0):
            #在未分配点中找与车场最近的点作为起始点，构成初始解，计算花费
            distance,index = self.find_nearest_custom_in_list(0,not_inserted)
            has_inserted.append(index)
            not_inserted.remove(index)
            init_serve = self.assign_list[index-1]
            #循环遍历未插入点，找使花费值增长最小的出入点以及插入位置，同时检查解的可行性
            min_inc_cost = float('inf')
            min_inc_ins_pos = -1
            min_inc_cus_ind = -1
            test_serve = copy.deepcopy(init_serve)
            while(len(not_inserted) != 0):
                min_inc_cost = float('inf')
                min_inc_ins_pos = -1
                min_inc_cus_ind = -1
                buff_serve = copy.deepcopy(test_serve)
                for ins_pos in range(3,len(test_serve)):
                    for cus_ind in not_inserted:
                        #找一个buff，保持原列表不变
                        buff_serve = copy.deepcopy(test_serve)
                        buff_serve.insert(ins_pos,cus_ind)
                        suit_distance,suit_time_window,new_serve = self.construct_avai(buff_serve)
                        if suit_distance & suit_time_window == 0:
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
                    self.assign_list_final.append(test_serve)
#                    print(test_serve)
#                    print(len(not_inserted))
                    break
                #若找到了，构造新的解，加入到结果中，并在not inserted中删掉
                else:
                    test_serve.insert(min_inc_ins_pos,min_inc_cus_ind)
                    suit_distance,suit_time_window,new_serve = self.construct_avai(test_serve)
                    has_inserted.append(min_inc_cus_ind)
                    not_inserted.remove(min_inc_cus_ind)
                    test_serve = new_serve
#            print("while finished")
            #find nearest里面要加上0，代价加上等待代价
            #也要把0加入到待插入列表中，但是插入后不能删除
            
    def construct_avai(self,serve):
        #此函数构造可行解，首先车辆容量，再检查距离约束，再检查时间窗约束
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
        for i in range(len(self.assign_list_final)):
            assign_str = ''
            for j in range(2,len(self.assign_list_final[i])-1):
                assign_str = assign_str + '%d'%(self.assign_list_final[i][j]) +';'
            assign_str = assign_str + '0'
            total_cost,current_time,distance,trans_cost,charge_cost,wait_cost,static_cost,charge_time = self.cal_cost(self.assign_list_final[i])
            result_string = ['DP%04d'%(i+1),'%d'%(self.assign_list_final[i][0]+1),assign_str,time.strftime('%H:%M',time.localtime(self.assign_list_final[i][1])), time.strftime('%H:%M',time.localtime(current_time)),\
                            '%d'%(distance) , '%.2f'%(trans_cost) , '%d'%(charge_cost) , '%.2f'%(wait_cost) , '%d'%(static_cost) , '%.2f'%(total_cost) , '%d'%(charge_time)]
            if i==0:
                print(result_string)
            csv_write.writerow(result_string)
    
if __name__ == '__main__':
    print("start",datetime.datetime.now())
    a = solution()
    print("load data finish and begin construct answer",datetime.datetime.now())
    a.insert()
    print("finish",datetime.datetime.now())
    for item in a.assign_list_final:
        print(item)
    a.write_csv()