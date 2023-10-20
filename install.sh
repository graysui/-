#!/bin/bash

# 更新系统包列表
sudo apt update

# 安装Python3和pip3
sudo apt install -y python3 python3-pip git

# 安装Python的watchdog库
pip3 install watchdog

# 拉取代码
git_repo="https://github.com/graysui/softlink.git"
destination_folder="softlink"

if [ -d "$destination_folder" ]; then
    echo "Directory $destination_folder already exists. Pulling latest changes..."
    cd $destination_folder
    git pull origin master
else
    git clone $git_repo $destination_folder
    cd $destination_folder
fi

# 提醒用户
echo "请修改softlink.py内的监控目录和目标目录"

