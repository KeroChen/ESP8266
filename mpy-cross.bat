@echo off
cls
Setlocal enabledelayedexpansion
:main
set /p filename=�����뵱ǰ·����Ҫ������ļ���(����Ĭ��webserver.py): 
if NOT DEFINED filename (
    set filename=webserver.py
)
if NOT exist %filename% (
    echo �ļ������ڣ����������룡
    PAUSE
    cls
    set filename=
    goto main
) else (
    echo ��ʼԤ����%filename%......
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
echo ����ɹ���
echo ���ɵĶ������ļ���׺Ϊmpy