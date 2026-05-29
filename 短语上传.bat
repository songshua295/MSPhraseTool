@echo off
chcp 65001 >nul
python main.py export

python main.py convert -f csv -i 自定义短语.csv

python main.py upload
pause