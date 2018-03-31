#coding=utf-8
import socket
import time

###同步路由器返回的网络时间，有误差
month_data = ['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun', 'Jul', 'Aug', 'Sept', 'Oct', 'Nov', 'Dec']
week_data = ['Mon', 'Tues', 'Wed', 'Thu', 'Fri', 'Sat', 'Sun']
host = "119.28.41.133"
post = 80

def get_date(inp):
    s = socket.socket(socket.AF_INET,socket.SOCK_STREAM)
    s.connect((host,post))
    s.sendall("""GET / HTTP/1.1\r\nHost: %s\r\nConnection: close\r\nUser-Agent: Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/65.0.3325.181 Safari/537.36\r\nAccept: text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,image/apng,*/*;q=0.8\r\nAccept-Language: zh-CN,zh;q=0.8,zh-TW;q=0.7,zh-HK;q=0.5,en-US;q=0.3,en;q=0.2\r\nAccept-Encoding: gzip, deflate\r\n\r\n""" % (host))
    data = s.recv(512)
    #print(data)    #Debug mode
    s.close()
    len_beg = data.find(b'Date: ') + 6
    len_end = data.find(b' GMT\r\n',len_beg)
    len = len_end - len_beg
    if len_end != -1:
        gmt_date = data[len_beg:len_end]
        #print(gmt_date)    #Debug mode
        #gmt_date = "Sat, 24 Mar 2018 05:42:17"   #Debug mode
        day = int(gmt_date[5:7])
        for m in [0,1,2,3,4,5,6,7,8,9,10,11]:
            if gmt_date.find(bytes(month_data[m], 'utf-8')) != -1:
            #if gmt_date.find(bytes(month_data[m])) != -1:      #python2 version
                month = m + 1
                break
        for w in [0,1,2,3,4,5,6]:
            if gmt_date.find(bytes(week_data[w], 'utf-8')) != -1:
            #if gmt_date.find(bytes(week_data[w])) != -1:       #python2 version
                week = w
                break
        year = int(gmt_date[len - 13:len - 9])
        bj_hour = int(gmt_date[len - 8:len - 6]) + 8   #北京时间 GMT+8:00:00
        hour = int(gmt_date[len - 8:len - 6])          #格林时间 GMT
        min = int(gmt_date[len - 5:len - 3])
        sec = int(gmt_date[len - 2:len])
    nor_date = [year, month, day, 0, hour, min, sec, 0, week]
    bj_date = [year, month, day, 0, bj_hour, min, sec, 0, week]
    if inp == "gmt+8":
        return bj_date
    elif inp == 'gmt':
        return nor_date