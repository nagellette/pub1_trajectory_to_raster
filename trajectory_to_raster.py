from osgeo import gdal
import psycopg2

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

for x in range(0, raster_x_count):
    for y in range(0, raster_y_count):
        previous_x = raster_x_corner + ((x - 1.0) * raster_x_step)
        previous_y = raster_y_corner + ((y - 1.0) * raster_y_step)
        current_x = raster_x_corner + (x * raster_x_step)
        current_y = raster_y_corner + (y * raster_y_step)

        query = "SELECT avg(geolife_trajectories.speed) FROM geolife_trajectories WHERE ST_Contains(ST_Transform(ST_MakeEnvelope(" \
                + str(previous_x) + "," + str(previous_y) + "," + str(current_x) + "," + str(current_y) + \
                ", 32650) ,4326), geolife_trajectories.geom) group by geolife_trajectories.speed;"

        cursor.execute(query)
        test = cursor.fetchall()
        if len(test) > 0:
            print(test)
