#!/bin/bash
# [ -d $2 ] || mkdir $2

inputfile=images/themis_images.csv

OLDIFS=$IFS
IFS=","
# delete the first line from the file containing column names
sed 1d $inputfile | while read name url lat_min lat_max long_min long_max width heigh scale res
do
        if [ -f images/themis_full/${name}.jpg ]; then
		convert -monitor -limit area 0 -limit map 0 images/themis_full/${name}.jpg -crop 1280x960 \
		-define png:color-type=2 -set filename:tile "%[fx:page.x/1280]_%[fx:page.y/960]" \
		+repage +adjoin "images/themis_crops/${name}_%[filename:tile].png"
        else
                echo ${name}.jpg does not exist
        fi
done

IFS=$OLDIFS

#/usr/bin/convert $1 -crop 1280x960 \
#    -debug cache -define png:color-type=2 -set filename:tile "%[fx:page.x/1280]_%[fx:page.y/960]" \
#    +repage +adjoin "crops/$2_%[filename:tile].png"
