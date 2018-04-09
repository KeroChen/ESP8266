# -*- coding: utf-8 -*- 
import network
import ntptime
import sys
import socket
import time
import machine
from machine import Pin

ap_if = network.WLAN(network.AP_IF)
ap_if.config(essid="Light", authmode=network.AUTH_WPA_WPA2_PSK, password="63423light")
wlan = network.WLAN(network.STA_IF)
wlan.active(True)
wlan.connect('K2P','415038973')
machine.freq(160000000)     #超频至160MHz，性能上暂时看不出有何提升

p4 = Pin(4, Pin.OUT)
#p5 = Pin(5, Pin.OUT)     #备用IO口
#p12 = Pin(12, Pin.OUT)
#p14 = Pin(14, Pin.OUT)
header_200 = """HTTP/1.1 200 OK\r\n%s\r\nServer: K-httpd\r\nContent-Type: %s\r\nConnection: keep-alive\r\nConent-Length: %s\r\n\r\n"""
header_404 = """HTTP/1.1 404 Not Found\r\n%s\r\nServer: K-httpd\r\nContent-Type: %s\r\nConnection: close\r\nConent-Length: %s\r\n\r\n"""
content_type = ["text/html; charset=utf-8", "text/css; charset=utf-8", "application/x-javascript; charset=utf-8", "image/x-icon", "image/jpeg", "image/png"]
ntptime.host = 'cn.ntp.org.cn'

host = '0.0.0.0'
port = 80
addr = socket.getaddrinfo(host, port)[0][-1]
s = socket.socket(socket.AF_INET,socket.SOCK_STREAM)
s.setblocking(1)
s.bind(addr)
s.listen(10)
print('Listening on', addr)

def ip_status():   #判断是否连接了路由器
    ip = wlan.ifconfig()
    if ip[1] != '0.0.0.0':
        try:
            return time.localtime(ntptime.time())
        except OSError:
            return '校对操作过快，请稍后再试！'
    else:
        return 'Unconnected'

def getlocaltime():
    month_data = ['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun', 'Jul', 'Aug', 'Sept', 'Oct', 'Nov', 'Dec']
    week_data = ['Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat', 'Sun']
    global t
    t = list(time.localtime())
    for m in [1,2,3,4,5,6,7,8,9,10,11,12]:
        if t[1] == m:
            month = month_data[m - 1]
            break
    for w in [0,1,2,3,4,5,6]:
        if t[6] == w:
            week = week_data[w]
            break
    if t[3] < 10:
        t[3] = "%s%s" % ("0",t[3])
    if t[4] < 10:
        t[4] = "%s%s" % ("0",t[4])
    if t[5] < 10:
        t[5] = "%s%s" % ("0",t[5])
    global local_date
    local_date = "Date: %s, %s %s %s %s:%s:%s GMT" % (week, t[2], month, t[0], t[3], t[4], t[5])

def writefiledata(filename, status, filedata):     #写文件数据
    f = open(filename, status)
    f.write(filedata)
    f.close()

def readfilesize(filename):     #读文件长度
    f = open(filename, 'r')
    f.seek(0,0)
    f.seek(0,2)
    return f.tell()
    f.close()

def readandsend_data(filename, add_str):     #读取文件数据并发送
    f = open(filename, 'r')
    while True:
        send_data = f.read(536)
        if len(send_data) == 0:
            break
        if send_data.find("%s") != -1:
            try:
                cl.sendall(send_data % (add_str))
            except:
                return 0
        else:
            try:
                cl.sendall(send_data)
            except:
                return 0
    f.close()

while True:     #主体
    try:
        cl, addr = s.accept()
    except OSError:
        print("OSError: line 92")
    #print('client connected from', addr)     #Debug mode
    data = cl.recv(1024)
    #print(data)     #Debug mode
    getlocaltime()
    #print(local_date)     #Debug mode
    if data.find(b'GET / HTTP') != -1:     #主页
        if p4.value() == 1:
            status = '开启'
        else:
            status = '关闭'
        cl.sendall("%s" % (header_200 % (local_date, content_type[0], readfilesize("/html/index.html") + len(status))))
        readandsend_data("/html/index.html", status)
    elif data.find(b'GET /upload ') != -1:     #文件上传
        cl.sendall("%s" % (header_200 % (local_date, content_type[0], readfilesize("/html/upload.html"))))
        readandsend_data("/html/upload.html", '')
    elif data.find(b'POST /upload ') != -1:     #文件POST提交
        datalen_beg = data.find(b'Content-Length: ') + 16
        datalen_end = data.find(b'\r\n', datalen_beg)
        datalen = int(data[datalen_beg:datalen_end])
        boundary_beg = data.find(b'boundary=') + 9
        boundary_end = data.find(b'\r\n', boundary_beg)
        boundary = data[boundary_beg:boundary_end]
        boundary_len = len(boundary)
        #print(datalen)     #Debug mode
        #print(boundary)     #Debug mode
        filestatus = False
        datafound = False
        v = 0
        while True:
            v = v + 1
            receives = cl.recv(1024)
            #print(receives)     #Debug mode
            #if receives.find(b'--' + boundary + b'\r\n') != -1:
            receives_beg = receives.find(b'--' + boundary + b'\r\n')     #寻找数据结构开头并计算长度
            package_len = len(receives)
                #print(package_len)     #Debug mode
            if receives.find(b'filename="') != -1 and filestatus == False:     #寻找文件名
                filename_beg = receives.find(b'filename="', receives_beg) + 10
                filename_end = receives.find(b'"\r\n', filename_beg)
                upload_filename = bytes.decode(receives[filename_beg:filename_end], 'utf-8')
                filestatus = True
                print(upload_filename)     #Debug mode
            if filestatus == True and receives.find(b'\r\n\r\n', filename_end) != -1 and datafound == False:     #寻找文件数据开头
                upload_contect_beg = receives.find(b'\r\n\r\n', filename_end) + 4
                datafound = True
            elif datafound != True:
                v = v - 1
            if filestatus == True and receives.find(b'\r\n--' + boundary + b'--\r\n') != -1:     #寻找文件数据结尾
                upload_contect_end = receives.find(b'\r\n--' + boundary + b'--\r\n')
                if v == 1:
                    upload_contect = receives[upload_contect_beg:upload_contect_end]
                    #print(upload_contect)     #Debug mode
                    writefiledata(upload_filename, 'wb', upload_contect)
                    break
                elif v > 1:
                    upload_contect = receives[:upload_contect_end]
                    #print(upload_contect)     #Debug mode
                    writefiledata(upload_filename, 'ab', upload_contect)
                    break
            elif filestatus == True and datafound == True:
                residue_len = datalen % package_len
                receives_times = datalen // package_len
                #print(residue_len)     #Debug mode
                #print(v)     #Debug mode
                if residue_len != 0 and receives_times == v:
                    receives = receives + cl.recv(1024)
                    upload_contect_end = receives.find(b'\r\n--' + boundary + b'--\r\n')
                    upload_contect = receives[:upload_contect_end]
                    writefiledata(upload_filename, 'ab', upload_contect)
                    #print(receives[:upload_contect_end])     #Debug mode
                    break
                if v == 1:
                    #print(receives[upload_contect_beg:])     #Debug mode
                    writefiledata(upload_filename, 'wb', receives[upload_contect_beg:])
                elif v > 1:
                    #print(bytes.decode(receives))     #Debug mode
                    writefiledata(upload_filename, 'ab', receives)
        upload_status = "文件上传成功！"
        cl.sendall("%s" % (header_200 % (local_date, content_type[0], readfilesize("/html/upload.html") + len(upload_status))))
        readandsend_data("/html/upload.html", upload_status)
    elif data.find(b'GET /favicon.ico ') != -1:     #网页图标
        cl.sendall("%s" % (header_200 % (local_date, content_type[3], readfilesize("/html/favicon.ico"))))
        f = open("/html/favicon.ico", 'rb')
        while True:
            icofile = f.read(536)
            if len(icofile) == 0:
                break
            cl.sendall(icofile)
        f.close()
    elif data.find(b'GET /off ') != -1:     #IO口低电平
        p4.value(0)
        cl.sendall("%s" % (header_200 % (local_date, content_type[0], readfilesize("/html/status.html") + len('已关灯！'))))
        readandsend_data("/html/status.html", '已关灯！')
        print("Controller(turn off):", addr)     #Debug mode
    elif data.find(b'GET /on ') != -1:     #IO口高电平
        p4.value(1)
        cl.sendall("%s" % (header_200 % (local_date, content_type[0], readfilesize("/html/status.html") + len('已开灯！'))))
        readandsend_data("/html/status.html", '已开灯！')
        print("Controller(turn on):", addr)     #Debug mode
    elif data.find(b'GET /synctime ') != -1:     #时间校对
        utc_time = ip_status()
        if utc_time != 'Unconnected' and utc_time != '校对操作过快，请稍后再试！':
            utc_time = list(utc_time[0:3] + (0,) + utc_time[3:6] + (0,))
            #print(utc_time)     #Debug mode
            machine.RTC().datetime(utc_time)
            if utc_time[1] < 10:
                utc_time[1] = "%s%s" % ("0", utc_time[1])
            if utc_time[2] < 10:
                utc_time[2] = "%s%s" % ("0", utc_time[2])
            if (utc_time[4] + 8) < 10:
                utc_time[4] = "%s%s" % ("0", utc_time[4] + 8)
            else:
                utc_time[4] = str(utc_time[4] + 8)
            if utc_time[5] < 10:
                utc_time[5] = "%s%s" % ("0", utc_time[5])
            if utc_time[6] < 10:
                utc_time[6] = "%s%s" % ("0", utc_time[6])
            addtime = """时间已校准！</b><br><br><b>当前北京时间是：<spen style="color:red;">%s年%s月%s日 %s:%s:%s</spen>""" % (str(utc_time[0]), utc_time[1], utc_time[2], utc_time[4], utc_time[5], utc_time[6])
            cl.sendall("%s" % (header_200 % (local_date, content_type[0], (readfilesize("/html/status.html") + len(addtime)))))
            readandsend_data("/html/status.html", addtime)
        elif utc_time == '校对操作过快，请稍后再试！':
            errno110_msg = utc_time + "</b>"
            cl.sendall("%s" % (header_200 % (local_date, content_type[0], (readfilesize("/html/status.html") + len(errno110_msg)))))
            readandsend_data("/html/status.html", errno110_msg)
        else:
            network_status = '时间校准失败，网络未连接！'
            cl.sendall("%s" % (header_200 % (local_date, content_type[0], (readfilesize("/html/status.html") + len(network_status)))))
            readandsend_data("/html/status.html", network_status)
    elif data.find(b'GET /') != -1:     #404找不到
        print(bytes.decode(data, 'utf-8'))
        len_beg = data.find(bytes("Host: ", 'utf-8')) + 6
        len_end = data.find(bytes("\r\n", 'utf-8'), len_beg)
        url_beg = data.find(bytes("GET ", 'utf-8')) + 4
        url_end = data.find(bytes(" HTTP/", 'utf-8'))
        msg_404 = "%s%s" % (bytes.decode(data[len_beg:len_end], 'utf-8'), bytes.decode(data[url_beg:url_end], 'utf-8')) ,t[0], t[1], t[2], t[3], t[4], t[5]
        cl.sendall("%s" % (header_404 % (local_date, content_type[0], readfilesize("/html/404.html") + len(msg_404))))
        readandsend_data("/html/404.html", msg_404)
    #print(data)     #Debug mode
    #print(addr,'client disconnected')     #Debug mode
    print('Close', addr)     #Debug mode
    cl.close()