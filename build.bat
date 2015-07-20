@echo off

REM Playscii windows EXE build batch

REM Build needs to know where your python and SDL2 dll are, modify
REM the two lines below as needed:
set PYTHONPATH="c:\Python34"
set SDLPATH=".\"

echo Removing old build...
rmdir /S /Q dist\
mkdir dist

echo Creating new build...
python setup.py py2exe

echo Copying PyOpenGL libs to build dir...
mkdir dist\OpenGL
xcopy /e /v /Q "%PYTHONPATH%\Lib\site-packages\OpenGL\*.*" dist\OpenGL\
del /s /Q dist\OpenGL\*.pyc
del /s /Q dist\OpenGL\*.pyo

echo Copying SDL2.dll...
copy %SDLPATH%\SDL2.dll dist\

echo Copying Playscii data files...
mkdir dist\art
copy /v art\*.* dist\art\
mkdir dist\charsets
copy /v charsets\*.* dist\charsets\
mkdir dist\docs
copy /v docs\*.* dist\docs\
mkdir dist\palettes
copy /v palettes\*.* dist\palettes\
mkdir dist\scripts
copy /v scripts\*.* dist\scripts\
mkdir dist\shaders
copy /v shaders\*.* dist\shaders\
REM test game content
mkdir dist\games
mkdir dist\games\test1
mkdir dist\games\test1\art
mkdir dist\games\test1\palettes
mkdir dist\games\test1\scripts
copy /v games\test1\*.* dist\games\test1\
copy /v games\test1\art\*.* dist\games\test1\art\
copy /v games\test1\palettes\*.* dist\games\test1\palettes\
copy /v games\test1\scripts\*.* dist\games\test1\scripts\
mkdir dist\games\cronotest
mkdir dist\games\cronotest\art
mkdir dist\games\cronotest\palettes
mkdir dist\games\cronotest\scripts
copy /v games\cronotest\*.* dist\games\cronotest\
copy /v games\cronotest\art\*.* dist\games\cronotest\art\
copy /v games\cronotest\palettes\*.* dist\games\cronotest\palettes\
copy /v games\cronotest\scripts\*.* dist\games\cronotest\scripts\
REM ignore ui art source assets (eg .xcf)
mkdir dist\ui
copy /v ui\*.png dist\ui\
copy readme.txt dist\
copy license.txt dist\
copy code_of_conduct.txt dist\
copy playscii.cfg.default dist\
copy binds.cfg.default dist\

echo Done!
pause
