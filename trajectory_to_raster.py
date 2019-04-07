from osgeo import gdal, osr
import psycopg2
import numpy as np
from datetime import datetime

## path to label raster
raster_path_label = './data/bejing_reduced_projected_labels.tif'


## extend function
def GetExtent(gt, cols, rows):
    ''' Return list of corner coordinates from a geotransform

        @type gt:   C{tuple/list}
        @param gt: geotransform
        @type cols:   C{int}
        @param cols: number of columns in the dataset
        @type rows:   C{int}
        @param rows: number of rows in the dataset
        @rtype:    C{[float,...,float]}
        @return:   coordinates of each corner

    Source: https://gis.stackexchange.com/questions/57834/how-to-get-raster-corner-coordinates-using-python-gdal-bindings
    '''
    ext = []
    xarr = [0, cols]
    yarr = [0, rows]

    for px in xarr:
        for py in yarr:
            x = gt[0] + (px * gt[1]) + (py * gt[2])
            y = gt[3] + (px * gt[4]) + (py * gt[5])
            ext.append([x, y])
        yarr.reverse()
    return ext


## read template raster file
print(raster_path_label)
raster_label = gdal.Open(raster_path_label)
raster_label_band = raster_label.GetRasterBand(1)

## get pixel counts by axis
raster_x_count = raster_label.RasterXSize
raster_y_count = raster_label.RasterYSize

## get transformation parameters
raster_label_geo_transform = raster_label.GetGeoTransform()

## get template corner coordinates
raster_x_corner = raster_label_geo_transform[0]
raster_y_corner = raster_label_geo_transform[3]

## get template pixel size by axis
raster_x_step = raster_label_geo_transform[1]
raster_y_step = raster_label_geo_transform[5]

## print raster extend and transformation parameters
print(raster_label_geo_transform)
print(GetExtent(raster_label_geo_transform, raster_x_count, raster_y_count))

## connect to postgresql for trajectory queries
with psycopg2.connect(database="nagellette-ws", user="test", password="123456", host="localhost",
                      port="5432") as connection:
    print("Connected succesfully to postgresql!")
cursor = connection.cursor()

## create empty arrays for raster bands
trajectory_count = np.zeros((raster_y_count, raster_x_count), dtype=np.float32)
speed_avg = np.zeros((raster_y_count, raster_x_count), dtype=np.float32)
speed_stddev = np.zeros((raster_y_count, raster_x_count), dtype=np.float32)
speed_variance = np.zeros((raster_y_count, raster_x_count), dtype=np.float32)

## create empty raster with 4 bands to produce final raster
output_raster = gdal.GetDriverByName('GTiff').Create('./data/output_trajectory.tif', raster_x_count, raster_y_count, 4,
                                                     gdal.GDT_Float32)
output_raster.SetGeoTransform(raster_label_geo_transform)
srs = osr.SpatialReference()
srs.ImportFromEPSG(32650)
output_raster.SetProjection(srs.ExportToWkt())  # Exports the coordinate system to the file

## counter for progress
counter = 0.0
total_count = float(raster_y_count) * float(raster_x_count)

## time function for time progress
start = datetime.now()
print("Process started at ", start)

## iterate over raster pixel design
for x in range(0, raster_x_count):
    for y in range(0, raster_y_count):

        ## create bounding box boundaries
        previous_x = raster_x_corner + ((x - 1.0) * raster_x_step)
        previous_y = raster_y_corner + ((y - 1.0) * raster_y_step)
        current_x = raster_x_corner + (x * raster_x_step)
        current_y = raster_y_corner + (y * raster_y_step)

        ## construct db query
        query = "SELECT count(geolife_trajectories.speed), " \
                "avg(geolife_trajectories.speed), " \
                "stddev(geolife_trajectories.speed), " \
                "variance(geolife_trajectories.speed) " \
                "FROM geolife_trajectories WHERE ST_Contains(ST_Transform(ST_MakeEnvelope(" \
                + str(previous_x) + "," + str(previous_y) + "," + str(current_x) + "," + str(current_y) + \
                ", 32650) ,4326), geolife_trajectories.geom);"

        ## run query, fetch output as list, fetch the tuple from list
        cursor.execute(query)
        query_output_list = cursor.fetchall()
        query_output = query_output_list[0]

        ## update template arrays with the calculatedd statistics
        if query_output[0] != 0:
            trajectory_count[y][x] = query_output[0]
            speed_avg[y][x] = query_output[1]
            speed_stddev[y][x] = query_output[2]
            speed_variance[y][x] = query_output[3]

        # print(x, y)
        print("{0:.0%}".format(counter / total_count), "Ellapsed time: ", datetime.now() - start)
        counter += 1.0

print(trajectory_count.shape)
print(speed_avg.shape)
print(speed_stddev.shape)
print(speed_variance.shape)

## fill the output bands
output_raster.GetRasterBand(1).WriteArray(trajectory_count)
output_raster.GetRasterBand(2).WriteArray(speed_avg)
output_raster.GetRasterBand(3).WriteArray(speed_stddev)
output_raster.GetRasterBand(4).WriteArray(speed_variance)

## close raster files
output_raster = None
raster_label = None

