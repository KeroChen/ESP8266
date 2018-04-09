# ESP8266
基于[**MicroPython**](http://www.micropython.org/)固件的Web控制

初学Python的第一个程序，也是初学MCU的第一个“大”程序，逻辑比较乱

1.0版本

功能：
- 控制GPIO口高低电平
- 校对模块RTC时钟
- 上传文件

注意：过大的python代码直接运行会发生内存请求失败错误，解决办法是预先编译为二进制文件。

编译工具：[mpy-cross](https://github.com/micropython/micropython/tree/master/mpy-cross)
