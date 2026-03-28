@echo off
setlocal

if not exist "spiberry\wheels" mkdir "spiberry\wheels"
tar -xzf "dependencies.tar.gz" -C "spiberry\wheels"
if errorlevel 1 exit /b 1

python -m zipapp -o spiberry.pyz .\spiberry -c