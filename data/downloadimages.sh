#!/bin/bash

inputfile=images/themis_images.csv

mkdir -p images/themis_full

OLDIFS=$IFS
IFS=","
# delete the first line from the file containing column names
sed 1d $inputfile | while read name url lat_min lat_max long_min long_max width heigh scale res
do
	if [ -f images/themis_full/${name}.jpg ]; then
		echo ${name}.jpg already exists
	else
		echo Downloading $name
		wget -O images/themis_full/${name}.jpg $url 
	fi
done 

IFS=$OLDIFS

#NAME,URL,LAT_MIN,LAT_MAX,LONG_MIN,LONG_MAX,WIDTH,HEIGHT,SCALE,RES
