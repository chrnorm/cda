#!/bin/bash
# [ -d $2 ] || mkdir $2

#DRAFT - current usage: ./cropctx.sh <ctx filename>


if [ -f images/ctx_full/$1 ]; then
	mkdir -p images/ctx_crops
	convert -monitor -limit area 0 -limit map 0 images/ctx_full/$1 -crop 1280x960 \
	-define png:color-type=2 -set filename:tile "%[fx:page.x/1280]_%[fx:page.y/960]" \
	+repage +adjoin "images/ctx_crops/${name}_%[filename:tile].png"
else
    echo $1 does not exist
fi

IFS=$OLDIFS

#/usr/bin/convert $1 -crop 1280x960 \
#    -debug cache -define png:color-type=2 -set filename:tile "%[fx:page.x/1280]_%[fx:page.y/960]" \
#    +repage +adjoin "crops/$2_%[filename:tile].png"
