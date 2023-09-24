#!/bin/bash

# /etc/supervisor/conf.d下に配置される設定ファイルを追加し、目的のプログラムを実行できるようにする。
# wineprefixを上書きし、任意の環境を挿入する

IMGNAME=matsu2254/wine64-x11-novnc-docker:latest
SPVCONF=`pwd`/WORK/supervisor/conf.d
WINEPRE=`pwd`/WORK/winepre
SPVSCRP=`pwd`/WORK/CODE

docker run -d --rm --name wine \
	-p 9090:8080 \
	-v $SPVCONF:/etc/supervisor/conf.d \
	-v $WINEPRE:/winepre \
        -v $SPVSCRP:/CODE \
	$IMGNAME
