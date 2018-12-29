@echo off
cls
Setlocal enabledelayedexpansion
:main
set /p filename=请输入当前路径下要编译的文件名(留空默认webserver.py): 
if NOT DEFINED filename (
    set filename=webserver.py
)
if NOT exist %filename% (
    echo 文件不存在，请重新输入！
    PAUSE
    cls
    set filename=
    goto main
) else (
    echo 开始预编译%filename%......
    echo=
    echo=
    echo -------------------------------------
    mpy-cross.exe %filename%
    if %errorlevel% == 0 (
        call :prompt
    ) else (
        if %filename%==webserver.py (
            call :prompt
        )
    )
    echo -------------------------------------
    echo=
    PAUSE
)
exit

:prompt
echo 编译成功！
echo 生成的二进制文件后缀为mpy