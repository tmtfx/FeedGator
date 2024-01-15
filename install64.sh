#!/bin/bash
echo "This will download and install feedparser to your system, continue? (type y or n)"
read text
if [ $text == "y" ]
then
echo
pkgman install feedparser_python310
ret3=$?
echo
else
	echo "Proceeding..."
	ret3=1
fi
echo "Do you wish to git clone & compile Haiku-PyAPI to your system? (type y or n)"
read text
if [ $text == "y" ]
then
git clone https://github.com/coolcoder613eb/Haiku-PyAPI.git
cd Haiku-PyAPI
jam -j$(nproc)
ret2=$?
cd ..
else
echo "Proceeding..."
ret2=1
fi
echo
if [ -e FeedGator.py ]
then
	if ![[ -e /boot/home/config/non-packaged/data/BGator2 ]]; then
		mkdir /boot/home/config/non-packaged/data/BGator2
	fi
	cp FeedGator.py /boot/home/config/non-packaged/data/BGator2
	ret4=$?
	if [ -e /boot/home/config/non-packaged/bin/FeedGator ]; then
		rm -f /boot/home/config/non-packaged/bin/FeedGator
	fi
	ln -s /boot/home/config/non-packaged/data/BGator2/FeedGator.py /boot/home/config/non-packaged/bin/FeedGator
	if ![[ -e /boot/home/config/settings/deskbar/menu/Applications/ ]]; then
		mkdir /boot/home/config/settings/deskbar/menu/Applications/
	fi
	if [ -e /boot/home/config/settings/deskbar/menu/Applications/FeedGator ]; then
		rm -f /boot/home/config/settings/deskbar/menu/Applications/FeedGator
	fi
	ln -s /boot/home/config/non-packaged/bin/FeedGator /boot/home/config/settings/deskbar/menu/Applications/FeedGator
	ret5=$?
else
	echo Main program missing
	ret4=1
	ret5=1
fi
echo
DIRECTORY=`pwd`/Data
if [ -d $DIRECTORY  ]
then
	cp -R Data /boot/home/config/non-packaged/data/BGator2
	ret6=$?
else
	echo Missing Data directory and images
	ret6=1
fi
echo


if [ $ret2 -lt 1 ]
then
	echo Installation of Haiku-PyAPI OK
else
	echo Installation of Haiku-PyAPI FAILED
fi
if [ $ret3 -lt 1 ]
then
	echo Installation of feedparser OK
else
	echo Installation of feedparser FAILED
fi
if [ $ret4 -lt 1 ] 
then
        echo Installation of FeedGator OK
else
        echo Installation of FeedGator FAILED
fi
if [ $ret5 -lt 1 ]
then
        echo Installation of menu entry OK
else
        echo Installation of menu entry FAILED
fi

if [ $ret6 -lt 1 ]
then
        echo Installation of Data files and images OK
else
        echo Installation of Data files and images FAILED
fi
