#!/bin/bash

# BASH script to convert PSD image files into map-projected ISIS CUBE files
# using the following website as a reference:
# https://isis.astrogeology.usgs.gov/fixit/projects/isis/wiki/Working_with_Mars_Reconnaissance_Orbiter_CTX_Data

numfiles=$(ls download/*.IMG | wc -l)
numdone=0

# make working directories if they don't exist
if [[ ! -e processing ]]; then
	mkdir processing
fi
if [[ ! -e mapped ]]; then
	mkdir mapped
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

	echo Map projecting ${fbname}	
	# the cam2map application converts a camera image to a map projected image
	cam2map from=processing/${fbname}.cal.cub map=sinusoidal_mojave.map to=mapped/${fbname}.mapped.cub pixres=map defaultrange=map
	# clean up
	rm processing/${fbname}.cal.cub

	# track how many are finished
	((numdone++))
	echo Completed ${numdone}/${numfiles}
done
