#!/bin/bash

# BASH script to convert PSD image files into map-projected ISIS CUBE files
# using the following website as a reference:
# https://isis.astrogeology.usgs.gov/fixit/projects/isis/wiki/Working_with_Mars_Reconnaissance_Orbiter_CTX_Data
#
# command line arguments:
# ./mapctx_equalized.sh <mapfile> <make seamless mosaic>
# where
# <mapfile> is the path to the USGS ISIS mapfile
# <make seamless mosaic> - if true, will call equalize and noseam programs to stitch the mosaic together. if false, will call automos to stitch the mosaic together.

# check for correct number of arguments
if [ "$#" -ne 2 ]; then
	echo "Usage: $0 <mapfile> <make seamless mosaic>" >&2
	exit 1
fi

# check that mapfile exists
if [[ ! -e $1 ]]; then
	echo "Mapfile $1 does not exist" >&2
	exit 1
fi

# check <make seamless mosaic> flag is either 1 or 0
if [ "$2" != "1" ] && [ "$2" != "0" ]; then
	echo "<make seamless mosaic flag> must be either 1 or 0, you entered $2" >&2
	exit 1
fi

numfiles=$(ls download/*.IMG | wc -l)
numdone=0

output=output-`date "+%Y-%m-%d-%H:%M:%S"`

# make working directories if they don't exist
if [[ ! -e processing ]]; then
	mkdir processing
fi
if [[ ! -e mapped ]]; then
	mkdir mapped
fi
if [[ ! -e ${output} ]]; then
	mkdir ${output}
fi

for filename in download/*.IMG; do
	fbname=$(basename "$filename" .IMG)

	echo Converting ${fbname}.IMG to ${fbname}.cub
	# importing CTX data and converting to ISIS .cub format 
	mroctx2isis from=download/${fbname}.IMG to=processing/${fbname}.cub

	echo Adding SPICE information to ${fbname}.cub
	# use spiceinit to add MRO SPICE data to the file
	spiceinit from=processing/${fbname}.cub

	echo Calibrating ${fbname}
	# ctxcal: radiometrically calibrates CTX images
	ctxcal from=processing/${fbname}.cub to=processing/${fbname}.cal.cub
	# clean up
	rm processing/${fbname}.cub

	# remove even/odd detector striping
	ctxevenodd from=processing/${fbname}.cal.cub to=processing/${fbname}.eo.cal.cub
	# clean up
	rm processing/${fbname}.cal.cub

	echo Map projecting ${fbname}	
	# the cam2map application converts a camera image to a map projected image
	cam2map from=processing/${fbname}.eo.cal.cub map=$1 to=mapped/${fbname}.mapped.cub pixres=map defaultrange=map
	# clean up
	rm processing/${fbname}.eo.cal.cub

	# track how many are finished
	((numdone++))
	echo Completed ${numdone}/${numfiles}
done

# create mosaic: check whether user wants seamless mosaic
if [ "$2" = "1" ]; then

	# create list of all map projected images
	cd mapped 
	ls -d -1 $PWD/*.* > ../${output}/allmapped.lis
	cd ..

	# create 'hold list' - this is the image the equalization shall be based from
	# first image is selected to be held
	cat ${output}/allmapped.lis | head -n 1 > ${output}/hold.lis

	# equalize map projected images
	equalizer fromlist=${output}/allmapped.lis holdlist=${output}/hold.lis

	# create list of all equalized images
	cd mapped
	ls -d -1 $PWD/*equ*.cub > ../${output}/equ.lis
	cd ..

	# create noseam mosaic of the images
	noseam fromlist=${output}/equ.lis to=${output}/mosaic_equ.cub samples=73 lines=73
else
	# create automos mosaic of the images
	automos fromlist=${output}/allmapped.lis mosaic=${output}/mosaic.cub
fi
