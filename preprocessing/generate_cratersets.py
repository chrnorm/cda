#!/usr/bin/env python
import pandas as pd
import cv2 as cv
import numpy as np
import sys
import ConfigParser
import os
import random

# Below parameters pertain to
# THEMIS_DayIR_ControlledMosaic_Iapygia_30S45E_100mpp.png
WIDTH = 26674.0
HEIGHT = 17783.0
EAST = 90.0
WEST = 45.0
SOUTH = -30.0
NORTH = 0.0
SCALE = 592.747  # pixels/degree
RES = 100  # m/pixel

# parameters for number of test and validation images
TEST_NUM = 1000
VAL_NUM = 1000

LAT_COL = 'LATITUDE_CIRCLE_IMAGE'
LNG_COL = 'LONGITUDE_CIRCLE_IMAGE'
DIAM_COL = 'DIAM_CIRCLE_IMAGE'


def getParams(parameter_file_name):
    print('[INFO] Opening cfg file: ' + parameter_file_name)
    parser = ConfigParser.RawConfigParser()
    ret = parser.read(parameter_file_name)
    parameters = dict()

    # if ret != parameter_file_name:
        # print('[ERROR] Could not open parameter file.')
        # sys.exit()
    for param in parser.items('image'):
        if param[0] == 'channel':
            parameters[param[0]] = int(param[1])
        else:
            parameters[param[0]] = param[1]
    for param in parser.items('bounds'):
        parameters[param[0]] = int(param[1])
    for param in parser.items('database'):
        parameters[param[0]] = param[1]
    print('[INFO] Parameters parsed:')
    print(parameters)
    return parameters


class SimpleCylindrical:
    """Projection class for simple cylindrical map projection. This is the
    projection used by THEMIS image. 
    """
    def __init__(self, n, s, e, w, scale, res):
        """n, s, e, w are lat lon bounds for the image to project to
        """
        self.north = n
        self.south = s
        self.east = e
        self.west = w
        self.scale = scale
        self.res = res
        return

    def latLngToPixel(self, lat, lng):
        x = (lng - self.west)*self.scale
        y = (self.north - lat)*self.scale
        return x, y

    def pixelToLatLng(self, x, y):
        lat = self.north - y/self.scale
        lng = self.west + x/self.scale
        return lat, lng


def readData(datafilename):
    global LAT_COL, LNG_COL, DIAM_COL
    from_csv = pd.read_csv(datafilename, sep='\t')
    return pd.DataFrame(from_csv, columns=[LAT_COL, LNG_COL, DIAM_COL])

def readImagesetData(datafilename):
    from_csv = pd.read_csv(datafilename)
    return pd.DataFrame(from_csv, columns=['NAME','URL','LAT_MIN',
        'LAT_MAX','LONG_MIN','LONG_MAX','WIDTH','HEIGHT','SCALE','RES'])


def plotGroundTruth(img, datafilename, latRange, lngRange):
    global LAT_COL, LNG_COL
    data = readData(datafilename)
    print(data[(data[LAT_COL] > 29.0) & (data[LNG_COL] < -44)])


def inLatLngRange(data, latRange, lngRange):
    global LAT_COL, LNG_COL
    mask = ((data[LAT_COL] >= latRange[0]) & (data[LAT_COL] <= latRange[1]) &
           (data[LNG_COL] >= lngRange[0]) & (data[LNG_COL] <= lngRange[1]))
    return data[mask]

def cropCrater(image, index, x, y, r, padding, xmin, xmax, ymin, ymax, imagestring):
    # setup coordinates of the bounding box to be exported
    # using the larger image pixel coordinate system
    x1 = x - r - padding
    x2 = x + r + padding
    y1 = y - r - padding
    y2 = y + r + padding

    # check that the bounding box does not exceed the edges of the image
    if x1 >= xmin and x2 <= xmax and y1 >= ymin and y2 <= ymax:
        # get the bounding box in the smaller image pixel coordinates
        x1_crop = x1 - xmin
        x2_crop = x2 - xmin
        y1_crop = y1 - ymin
        y2_crop = y2 - ymin
        crop_image = image[y1_crop:y2_crop, x1_crop:x2_crop]
        crop_filename = '../data/images/themis_windowed/' + imagestring + '_' + str(index) + '.png'
        cv.imwrite(crop_filename, crop_image)


def main():
    global LAT_COL, LNG_COL, DIAM_COL, SCALE, RES, NORTH, SOUTH, EAST, WEST, TEST_NUM, VAL_NUM
    params = getParams(sys.argv[1])

    data = readData(params['data_filename'])
    imagesetdata = readImagesetData('../data/images/themis_images.csv')
    # print imagesetdata['NAME'].iloc[1]

    # open JSON files to write crater windows to
    testfile = open('../data/jsons/test_boxes.json','w')
    valfile = open('../data/jsons/val_boxes.json','w')
    trainfile = open('../data/jsons/train_boxes.json','w')

    #one decimal format string
    one_decimal = "{0:0.1f}"
    # write the opening parentheses to the file
    testfile.write('[')
    valfile.write('[')
    trainfile.write('[')

    #index variable to keep track of how many total iterations
    total_index = 0

    #keep track of how many craters in total are in the data
    craters_train = 0
    craters_val = 0
    craters_test = 0

    total_image_num = len([filename for filename in os.listdir('../data/images/themis_crops')])
    random_image_indexes = random.sample(xrange(1, total_image_num), 2000)
    random.shuffle(random_image_indexes)
    val_image_indexes = sorted(random_image_indexes[:1000])
    test_image_indexes = sorted(random_image_indexes[-1000:])
    print test_image_indexes[0]

    print "test_image_indexes", test_image_indexes
    

    for i, imagename in enumerate(imagesetdata['NAME']):
        print i, imagename
        all_images = [filename for filename in os.listdir('../data/images/themis_crops') if filename.startswith(imagename)]
        print all_images

        # set up the projection object
        proj = SimpleCylindrical(imagesetdata['LAT_MAX'].iloc[i], imagesetdata['LAT_MIN'].iloc[i], 
            imagesetdata['LONG_MAX'].iloc[i], imagesetdata['LONG_MIN'].iloc[i], SCALE, RES)
        # print(pixelToLatLng(1000, 1000))

        # iterate through all images 
        for index, imagestring in enumerate(all_images):
            # open image to project database craters onto
            image = cv.imread('../data/images/themis_crops/'+imagestring)

            # get height and width from image
            imgheight, imgwidth = image.shape[:2]

            if imgheight != params['height'] or imgwidth != params['width']:
                continue

            # order of JSON file writing is testfile x200 -> valfile x200 -> trainfile x<remainder>
            # if total_index + index < TEST_NUM:
            if total_index in test_image_indexes:
                jsonfile = testfile
            # elif total_index + index < TEST_NUM + VAL_NUM:
            elif total_index in val_image_indexes:
                jsonfile = valfile
            else:
                jsonfile = trainfile

            # write image name to jsonfile

            if jsonfile == testfile and total_index != test_image_indexes[0]:
                jsonfile.write(',')
                print 'writing comma'
            if jsonfile == valfile and total_index != val_image_indexes[0]:
                jsonfile.write(',')
                print 'writing comma'
            if jsonfile == trainfile and total_index != 0:
                jsonfile.write(',')
                print 'writing comma'

            print jsonfile
            jsonfile.write('\n{\n"image_path": "themis_crops/'+imagestring+'",\n"rects": [')

            # image string is in format 'imagename_xmin_ymin.png', parse this into xmin and ymin ints
            x_index, y_index = [int(i) for i in imagestring[(len(imagename)+1):(len(imagestring)-len('.png'))].split('_')]

            # convert x and y index into coordinates using width and height from parameter file
            xmin = x_index * params['width']
            ymin = y_index * params['height']


            xmax = xmin + imgwidth
            ymax = ymin + imgheight
            print imagestring
            print 'xmin:', xmin, 'xmax:', xmax, 'ymin:', ymin, 'ymax:', ymax

            # turn the pixel boundaries of the image into lat and long values
            bounding_lat_1, bounding_lng_1 = proj.pixelToLatLng(xmax, ymax)
            bounding_lat_2, bounding_lng_2 = proj.pixelToLatLng(xmin, ymin)

            # sort the bounding lat/longs into ascending order - allows the
            # script to deal with negative values
            min_lat, max_lat = sorted((bounding_lat_1, bounding_lat_2))
            min_lng, max_lng = sorted((bounding_lng_1, bounding_lng_2))

            # print([min_lat, max_lat])
            # print([min_lng, max_lng])
            p = inLatLngRange(data, [min_lat, max_lat], [min_lng, max_lng])
            # print 'number of detected craters:', len(p)
            # p = inLatLngRange(data, [20.0, 30.0], [-45.0, -30.0])
            lats = [lat for lat in p[LAT_COL]]
            lngs = [lng for lng in p[LNG_COL]]
            diams = [diam for diam in p[DIAM_COL]]
            img_circled = image.copy()

            # variable to ensure commas are correctly written in the JSON file
            first_window = 1

            for index, latlng in enumerate(zip(lats, lngs)):
                # determine crater pixel location in the larger image
                x, y = proj.latLngToPixel(latlng[0], latlng[1])
                # determine the crater pixel location in the cropped image
                crop_x = x - xmin
                crop_y = y - ymin

                # print("x = ", x, ", y = ", y)
                r_float = 1.0e3*diams[index]/(2.0*RES)
                r = int(round(r_float))

                # get window coordinates
                x1 = int(np.floor(crop_x - r_float*1.15))
                x2 = int(np.ceil(crop_x + r_float*1.10))
                y1 = int(np.floor(crop_y - r_float*1.15))
                y2 = int(np.ceil(crop_y + r_float*1.10))

                # check that the bounding box does not exceed the edges of the image
                if x1 >= 0 and x2 <= imgwidth and y1 >= 0 and y2 <= imgheight:
                    # get the bounding box in the smaller image pixel coordinates

                    if jsonfile == testfile:
                        craters_test += 1
                    elif jsonfile == valfile:
                        craters_val += 1
                    else:
                        craters_train += 1

                    if first_window:
                        first_window = 0
                    else:
                        jsonfile.write(',')

                    jsonfile.write('\n{\n')
                    jsonfile.write('"x1": ' + one_decimal.format(x1) + ',\n')
                    jsonfile.write('"x2": ' + one_decimal.format(x2) + ',\n')
                    jsonfile.write('"y1": ' + one_decimal.format(y1) + ',\n')
                    jsonfile.write('"y2": ' + one_decimal.format(y2) + '\n}')
                    cv.rectangle(img_circled, (x1,y1), (x2,y2), (0, 0, 255), 1, 8, 0)
                    # cv.circle(img_circled, (int(round(crop_x)), int(round(crop_y))), r, (0, 0, 255))
                    # cropCrater(image, index, x, y, r, 5, xmin, xmax, ymin, ymax, imagestring)

            total_index += 1
            cv.imwrite('../data/images/themis_windowed/' + imagestring, img_circled)

            # write window end parentheses to JSON file
            jsonfile.write('\n]\n}')

        # update total index variable
        # total_index += len(all_images)
        print 'total_index',total_index

    # write EOF parenthesis to JSON files
    testfile.write('\n]')
    valfile.write('\n]')
    trainfile.write('\n]')

    print 'number of testing craters:', craters_test
    print 'number of validation craters:', craters_val
    print 'number of training craters:', craters_train
    return

if __name__ == '__main__':
    main()
