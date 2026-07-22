@echo off

mkdir .\bin
mkdir .\bin\Win32
mkdir .\bin\x64
xcopy /F /Y ..\..\lib\Win32\* .\bin\Win32\Debug\
xcopy /F /Y ..\..\lib\x64\* .\bin\x64\Debug\
xcopy /F /Y ..\..\lib\Win32\* .\bin\Win32\Release\
xcopy /F /Y ..\..\lib\x64\* .\bin\x64\Release\