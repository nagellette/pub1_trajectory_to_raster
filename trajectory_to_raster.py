from osgeo import gdal, ogr

## Path to work area boundary
work_area_shape = './data/bejing_work_area_projected.shp'
raster_path_label = './data/bejing_reduced_projected_labels.tif'

geo_driver = ogr.GetDriverByName("ESRI Shapefile")
work_area = geo_driver.Open(work_area_shape, 0)
work_area_layer = work_area.GetLayer()
work_area_extent = work_area_layer.GetExtent()

work_area_crs = work_area_layer.GetSpatialRef()

print(work_area_extent)
print(work_area_extent[0] - work_area_extent[1])

raster_label = gdal.Open(raster_path_label)
print(raster_label)
raster_label_band = raster_label.GetRasterBand(0)
raster_label_band_x = raster_label_band.RasterXSize
raster_label_extend = raster_label.GetGeoTransform()

print(raster_label_band_x)
