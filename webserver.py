# -*- coding: utf-8 -*- 
import network
import ntptime
import uos
import sys
import socket
import time
import machine
import ubinascii
import uhashlib
#import urequests
from machine import Pin
from machine import PWM

machine.freq(160000000) #超频至160MHz（实验性）
####################
#WIFI功能设置
ap_if = network.WLAN(network.AP_IF)
ap_if.config(essid="Light", authmode=network.AUTH_WPA_WPA2_PSK, password="lightpassword")
wlan = network.WLAN(network.STA_IF)
wlan.active(True)
wlan.connect('SSID','password')
####################

####################
#IO口初始化
p2 = Pin(2, Pin.OUT)    #板载LED
p2.value(1)

p4 = Pin(4, Pin.OUT)    #备用IO口

p5 = Pin(5, Pin.OUT)
pwm5 = PWM(p5)          #舵机PWM输出
pwm5.freq(50)
pwm5.duty(77)           #90度角

p12 = Pin(12, Pin.OUT)
pwm12 = PWM(p12)        #电机正转PWM输出&&三相无刷电机电调PWM输出
pwm12.freq(50)
pwm12.duty(51)          #0油门

p14 = Pin(14, Pin.OUT)
pwm14 = PWM(p14)        #电机反转PWM输出
pwm14.freq(50)
pwm14.duty(0)
####################

####################
#http协议头
header_101 = """HTTP/1.1 101 Web Socket Protocol Handshake\r\nUpgrade: websocket\r\nServer: K-httpd\r\nConnection: Upgrade\r\nSec-WebSocket-Accept: %s\r\n\r\n"""
header_200 = """HTTP/1.1 200 OK\r\n%s\r\nServer: K-httpd\r\nContent-Type: %s\r\nConnection: keep-alive\r\nConent-Length: %s\r\n\r\n"""
header_401 = """HTTP/1.1 401 Unauthorized\r\n%s\r\nServer: K-httpd\r\nWWW-Authenticate: Basic realm="ESP8266"\r\nContent-Type: %s\r\nConnection: close\r\n\r\n"""
header_404 = """HTTP/1.1 404 Not Found\r\n%s\r\nServer: K-httpd\r\nContent-Type: %s\r\nConnection: close\r\nConent-Length: %s\r\n\r\n"""
content_type = ["text/html; charset=utf-8", "text/css; charset=utf-8", "application/x-javascript; charset=utf-8", "image/x-icon", "image/jpeg", "image/png"]
ntptime.host = 'cn.ntp.org.cn'
magic_key = b"258EAFA5-E914-47DA-95CA-C5AB0DC85B11"
####################

####################
#Socket初始化（TCP）
host = '0.0.0.0'
port = 80
addr = socket.getaddrinfo(host, port)[0][-1]
s = socket.socket(socket.AF_INET,socket.SOCK_STREAM)
s.setblocking(True)
s.bind(addr)
s.listen(5)
####################

def ip_status():   #判断是否连接了路由器
    ip = wlan.ifconfig()
    if ip[1] != '0.0.0.0':
        try:
            return time.localtime(ntptime.time())
        except:
            return '校对操作过快，请稍后再试！'
    else:
        return 'Unconnected'

def getlocaltime():
    month_data = ['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun', 'Jul', 'Aug', 'Sept', 'Oct', 'Nov', 'Dec']
    week_data = ['Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat', 'Sun']
    global t
    try:
        t = list(time.localtime())
    except:
        print("Get local time error")
        return
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
    global error_file
    error_file = False
    try:
        f = open(filename, status)
    except error:
        print('Write failed', error)
        error_file = True
        return
    else:
        f.write(filedata)
        f.close()

def readfilesize(filename):     #读文件长度
    try:
        f = open(filename, 'r')
    except error:
        print('File open error', error)
    else:
        f.seek(0,0)
        f.seek(0,2)
        f_tell = f.tell()
        f.close()
        return f_tell

def readandsend_data(filename, r_status = 'r', add_str = ''):     #读取文件数据并发送
    if r_status == 'rb':
        r_binary = True
    else:
        r_binary = False
    try:
        f = open(filename, r_status)
    except error:
        print('File open error', error)
        return 'file error'
    while True:
        send_data = f.read(536)
        if len(send_data) == 0:
            break
        if r_binary == False and send_data.find("%s") != -1:
            try:
                cl.sendall(send_data % (add_str))
            except:
                print("Send have '%s' data error")
        else:
            try:
                cl.sendall(send_data)
            except:
                print('Send data error')
    f.close()

def parse_recv_data(msg):     #WebSocket报文解析
    en_bytes = b''
    cn_bytes = []
    if len(msg) < 6:
        return ''
    v = msg[1] & 0x7f
    if v == 0x7e:
        p = 4
    elif v == 0x7f:
        p = 10
    else:
        p = 2
    mask = msg[p:p + 4]
    data = msg[p + 4:]
    for k, v in enumerate(data):
        nv = chr(v ^ mask[k % 4])
        nv_bytes = nv.encode()
        nv_len = len(nv_bytes)
        if nv_len == 1:
            en_bytes += nv_bytes
        else:
            en_bytes += b'%s'
            cn_bytes.append(ord(nv_bytes.decode()))
    if len(cn_bytes) > 2:       #字节数组转汉字
        cn_str = ''
        clen = len(cn_bytes)
        count = int(clen / 3)
        for x in range(0, count):
            i = x * 3
            b = bytes([cn_bytes[i], cn_bytes[i + 1], cn_bytes[i + 2]])
            cn_str += b.decode()
        new = en_bytes.replace(b'%s%s%s', b'%s')
        new = new.decode()
        res = (new % tuple(list(cn_str)))
    else:
        res = en_bytes.decode()
    return res

def websocket_ctl(data_ws):
    if data_ws.find(b'Connection: Upgrade') != -1:
        client_key_beg = data_ws.find(b'Sec-WebSocket-Key:') + 19
        client_key_end = data_ws.find(b'\r\n', client_key_beg)
        client_key = data_ws[client_key_beg:client_key_end]
        #print('client_key:', client_key)     #Debug mode
        server_key = (ubinascii.b2a_base64(uhashlib.sha1(client_key + magic_key).digest()).decode('utf-8')).strip()
        #print('server_key:', server_key)     #Debug mode
        cl.sendall("%s" % (header_101 % (server_key)))
        print('[Info]: Open WebSocket!!!')
        while True:
            data = cl.recv(1024)
            #print(data)     #Debug mode
            msg = parse_recv_data(data)
            #print(msg)     #Debug mode
            if msg.find("control&go-value=") != -1:     #前进
                #go_value_beg = msg.find("control&go-value=") + 17
                #go_value_end = go_value_beg + 2
                go_value = int(msg[17:]) + 51
                pwm12.duty(go_value)
                print("go_value:", go_value)     #Debug mode
            if msg.find("control&turn-value=") != -1:       #左右
                #turn_value_beg = msg.find("control&turn-value=") + 19
                #turn_value_end = turn_value_beg + 2
                if int(msg[19:]) >= 26:      #右转
                    turn_value = int(msg[19:]) - 26
                    pwm5.duty(77 - turn_value)
                    print("turn_value:", (77 - turn_value))      #Debug mode
                if int(msg[19:]) < 26:      #左转
                    turn_value = int(~int(msg[19:]) + 26)
                    pwm5.duty(77 + turn_value)
                    print("turn_value:", (77 + turn_value))      #Debug mode
            if msg == "Close connection":       #正常关闭连接
                print('[Info]: Close WebSocket!!!')
                break
            elif msg == " ":     #非正常关闭连接
                print('[Warning]: Abnormal closure WebSocket!!!')
                break

#def bingimages():     #bing壁纸
#    req =  urequests.get('https://cn.bing.com/HPImageArchive.aspx?format=js&idx=0&n=1')
#    json_str = str(req.json()['images'])
#    url = 'https://cn.bing.com' + json_str[json_str.find("\'url\': \'") + 8:json_str.find("\'",json_str.find("\'url\': \'") + 8)]

def main():     #主体
    ban = 1
    global cl, addr
    time.sleep(2)
    utc_time = ip_status()
    if utc_time != 'Unconnected' and utc_time != '校对操作过快，请稍后再试！':
        utc_time = list(utc_time[0:3] + (0,) + utc_time[3:6] + (0,))
        machine.RTC().datetime(utc_time)
        print("GMT date: %s/%s/%s %s:%s:%s" % (utc_time[0], utc_time[1], utc_time[2], utc_time[4], utc_time[5], utc_time[6]))
    else:
        print('Network error')
    print('Listening on', addr)
    pwm5.duty(77)
    pwm12.duty(51)
    while True:
        try:
            cl, addr = s.accept()
        except OSError:
            print("OSError: accept")
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
            readandsend_data("/html/index.html", 'r', status)
            print('[Info]: GET /index.html')
        elif data.find(b'GET /upload ') != -1:     #文件上传
            if data.find(b'Authorization: Basic ') == -1:
                cl.sendall("%s" % (header_401 % (local_date, content_type[0])))
            elif data.find(b'Authorization: Basic ') != -1:
                base64_auth_beg = data.find(b'Authorization: Basic ') + 21
                base64_auth_end = data.find(b'\r\n', base64_auth_beg)
                base64_auth = data[base64_auth_beg:base64_auth_end]
                #print(base64_auth)     #Debug mode
                auth = ubinascii.a2b_base64(base64_auth).decode('utf-8')
                #print(auth)     #Debug mode
                #print('ban=', ban)     #Debug mode
                if auth == 'admin:123456':
                    cl.sendall("%s" % (header_200 % (local_date, content_type[0], readfilesize("/html/upload.html"))))
                    readandsend_data("/html/upload.html")
                elif ban != 5:
                    ban = ban + 1
                    cl.sendall("%s" % (header_401 % (local_date, content_type[0])))
                elif ban == 5:
                    #ban_ip_beg = data.find(bytes("Host: ", 'utf-8')) + 6
                    #ban_ip_end = data.find(bytes("\r\n", 'utf-8'), ban_ip_beg)
                    #ban_ip = bytes.decode(data[ban_ip_beg:ban_ip_end], 'utf-8')      #Ban IP
                    cl.sendall("%s" % (header_404 % (local_date, content_type[0], '0')))
            print('[Info]: GET /upload.html')
        elif data.find(b'POST /upload ') != -1:     #文件POST提交，注：不支持IE、Edge浏览器，提交的文件名太过奇葩
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
                receives_beg = receives.find(b'--' + boundary + b'\r\n')     #寻找数据结构开头并计算长度
                package_len = len(receives)
                    #print(package_len)     #Debug mode
                if receives.find(b'filename="') != -1 and filestatus == False:     #寻找文件名
                    filename_beg = receives.find(b'filename="', receives_beg) + 10
                    filename_end = receives.find(b'"\r\n', filename_beg)
                    upload_filename = bytes.decode(receives[filename_beg:filename_end], 'utf-8')
                    filestatus = True
                    print("Upload file name:", upload_filename)     #Debug mode
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
            if error_file == True:
                upload_status = "文件上传失败！请检查文件路径。"
            else:
                upload_status = "文件上传成功！"
            cl.sendall("%s" % (header_200 % (local_date, content_type[0], readfilesize("/html/upload.html") + len(upload_status))))
            readandsend_data("/html/upload.html", 'r', upload_status)
            print('[Info]: Upload success!!!')
        elif data.find(b'GET /favicon.ico ') != -1:     #网页图标
            cl.sendall("%s" % (header_200 % (local_date, content_type[3], (str(readfilesize("/html/favicon.ico")) + "\r\nCache-control: max-age=86400"))))
            readandsend_data("/html/favicon.ico", 'rb')
            print('[Info]: GET /favicon.ico')
        elif data.find(b'GET /off ') != -1:     #IO口低电平
            p4.value(0)
            cl.sendall("%s" % (header_200 % (local_date, content_type[0], readfilesize("/html/status.html") + len('已关灯！'))))
            readandsend_data("/html/status.html", 'r', '已关灯！')
            print('[Info]: GET /status.html')
            #print("Controller(turn off):", addr)     #Debug mode
        elif data.find(b'GET /on ') != -1:     #IO口高电平
            p4.value(1)
            cl.sendall("%s" % (header_200 % (local_date, content_type[0], readfilesize("/html/status.html") + len('已开灯！'))))
            readandsend_data("/html/status.html", 'r', '已开灯！')
            print('[Info]: GET /status.html')
            #print("Controller(turn on):", addr)     #Debug mode
        elif data.find(b'GET /control ') != -1:     #小车控制页面
            cl.sendall("%s" % (header_200 % (local_date, content_type[0], (str(readfilesize("/html/car.html.gz")) + "\r\nContent-Encoding: gzip\r\nCache-control: max-age=86400"))))
            readandsend_data("/html/car.html.gz", 'rb')
            pwm5.duty(77)
            pwm12.duty(51)
            print('[Info]: GET /car.html')
        elif data.find(b'GET /control_open ') != -1:     #请求websocket连接
            websocket_ctl(data)
        #elif data.find(b'GET /js/jquery.min.js ') != -1:    #jquery.min.js
        #    try:
        #        cl.sendall("%s" % (header_200 % (local_date, content_type[2], (str(readfilesize("/html/js/jquery.min.js.gz")) + "\r\nContent-Encoding: gzip\r\nCache-control: max-age=86400"))))
        #        readandsend_data("/html/js/jquery.min.js.gz", 'rb')
        #        print('GET /js/jquery.min.js')
        #    except:
        #        print('Send jquery.js error')
        elif data.find(b'GET /css/car.css ') != -1:    #car.css
            try:
                cl.sendall("%s" % (header_200 % (local_date, content_type[1], (str(readfilesize("/html/css/car.css.gz")) + "\r\nContent-Encoding: gzip\r\nCache-control: max-age=86400"))))
                readandsend_data("/html/css/car.css.gz", 'rb')
                print('[Info]: GET /css/car.css')
            except:
                print('Send car.css error')
        elif data.find(b'GET /css/index.css ') != -1:    #index.css
            try:
                cl.sendall("%s" % (header_200 % (local_date, content_type[1], (str(readfilesize("/html/css/index.css.gz")) + "\r\nContent-Encoding: gzip\r\nCache-control: max-age=86400"))))
                readandsend_data("/html/css/index.css.gz", 'rb')
                print('[Info]: GET /css/index.css')
            except:
                print('Send index.css error')
        elif data.find(b'GET /css/status.css ') != -1:    #status.css
            try:
                cl.sendall("%s" % (header_200 % (local_date, content_type[1], (str(readfilesize("/html/css/status.css.gz")) + "\r\nContent-Encoding: gzip\r\nCache-control: max-age=86400"))))
                readandsend_data("/html/css/status.css.gz", 'rb')
                print('[Info]: GET /css/status.css')
            except:
                print('Send status.css error')
        elif data.find(b'GET /css/upload.css ') != -1:    #upload.css
            try:
                cl.sendall("%s" % (header_200 % (local_date, content_type[1], (str(readfilesize("/html/css/upload.css.gz")) + "\r\nContent-Encoding: gzip\r\nCache-control: max-age=86400"))))
                readandsend_data("/html/css/upload.css.gz", 'rb')
                print('[Info]: GET /css/upload.css')
            except:
                print('Send upload.css error')
        elif data.find(b'GET /img/f-logo.png ') != -1:    #f-logo.png
            try:
                cl.sendall("%s" % (header_200 % (local_date, content_type[5], (str(readfilesize("/html/img/f-logo.png")) + "\r\nCache-control: max-age=86400"))))
                readandsend_data("/html/img/f-logo.png", 'rb')
                print('[Info]: GET /img/f-logo.png')
            except:
                print('Send f-logo.png error')
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
                addtime = """时间已校准！<br>当前北京时间是：<spen style="color:red;font-size: 15px;">%s年%s月%s日 %s:%s:%s</spen>""" % (str(utc_time[0]), utc_time[1], utc_time[2], utc_time[4], utc_time[5], utc_time[6])
                cl.sendall("%s" % (header_200 % (local_date, content_type[0], (readfilesize("/html/status.html") + len(addtime)))))
                readandsend_data("/html/status.html", 'r', addtime)
            elif utc_time == '校对操作过快，请稍后再试！':
                errno110_msg = utc_time + "</b>"
                cl.sendall("%s" % (header_200 % (local_date, content_type[0], (readfilesize("/html/status.html") + len(errno110_msg)))))
                readandsend_data("/html/status.html", 'r', errno110_msg)
            else:
                network_status = '时间校准失败，网络未连接！'
                cl.sendall("%s" % (header_200 % (local_date, content_type[0], (readfilesize("/html/status.html") + len(network_status)))))
                readandsend_data("/html/status.html", 'r', network_status)
            print('[Info]: GET /synctime')
        elif data.find(b'GET /') != -1:     #404找不到
            #print(bytes.decode(data, 'utf-8'))     #Debug mode
            len_beg = data.find(bytes("Host: ", 'utf-8')) + 6
            len_end = data.find(bytes("\r\n", 'utf-8'), len_beg)
            url_beg = data.find(bytes("GET ", 'utf-8')) + 4
            url_end = data.find(bytes(" HTTP/", 'utf-8'))
            msg_404 = "%s%s" % (bytes.decode(data[len_beg:len_end], 'utf-8'), bytes.decode(data[url_beg:url_end], 'utf-8')) ,t[0], t[1], t[2], (int(t[3]) + 8), t[4], t[5]
            cl.sendall("%s" % (header_404 % (local_date, content_type[0], readfilesize("/html/404.html") + len(msg_404))))
            readandsend_data("/html/404.html", 'r', msg_404)
            print('[Error]: 404 Not Found!!!')
        #print(data)     #Debug mode
        #print(addr,'client disconnected')     #Debug mode
        #print('Close', addr)     #Debug mode
        cl.close()

if __name__ == "__main__":
    main()