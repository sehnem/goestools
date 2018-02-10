from netCDF4 import Dataset
import numpy as np
from osgeo import osr
from osgeo import gdal
import time as t

# Define KM_PER_DEGREE
KM_PER_DEGREE = 111.32

var = 'CMI'

# nc.variables['goes_imager_projection']

# GOES-16 Extent (satellite projection) [llx, lly, urx, ury]
# GOES16_EXTENT = [-5434894.885056, -5434894.885056, 5434894.885056, 5434894.885056]
# GOES16_EXTENT = [-5434546.127484, 5434546.127484, -5434241.773362, 5434241.773362]


def exportImage(image, path):
    driver = gdal.GetDriverByName('netCDF')
    return driver.CreateCopy(path, image, 0)


def getGeoT(extent, nlines, ncols):
    # Compute resolution based on data dimension
    resx = (extent[1] - extent[0]) / ncols
    resy = (extent[3] - extent[2]) / nlines
    return [extent[0], resx, 0, extent[3], 0, -resy]


def remap(self):

    extent = self.area['extent']

    area_def = '+proj={} +h={} +a={} +b={} +lat_0=0.0 +lon_0={}+sweep={}' \
               '+no_defs'.format(self.area['proj'], self.area['h'], self.area['a'],
                                 self.area['b'], self.area['lon_0'], self.area['sweep'])


    sourcePrj = osr.SpatialReference()
    sourcePrj.ImportFromProj4(area_def)

    targetPrj = osr.SpatialReference()
    targetPrj.ImportFromProj4('+proj=longlat +ellps=WGS84 +datum=WGS84 +no_defs')

    # Build connection info based on given driver name
    connectionInfo = 'NETCDF:\"' + self.filename + '\":' + self.product


    # Open NetCDF file (GOES-16 data)
    raw = gdal.Open(connectionInfo, gdal.GA_ReadOnly)

    # Setup projection and geo-transformation
    raw.SetProjection(sourcePrj.ExportToWkt())
    raw.SetGeoTransform(getGeoT(extent, raw.RasterYSize, raw.RasterXSize))

    # Compute grid dimension
    sizex = int((extent[1] - extent[0]) * KM_PER_DEGREE/ self.resolution)
    sizey = int((extent[3] - extent[2]) * KM_PER_DEGREE/ self.resolution)

    # Get memory driver
    memDriver = gdal.GetDriverByName('MEM')

    # Create grid
    grid = memDriver.Create('grid', sizex, sizey, 1, gdal.GDT_Float32)

    # Setup projection and geo-transformation
    grid.SetProjection(targetPrj.ExportToWkt())
    grid.SetGeoTransform(getGeoT(extent, grid.RasterYSize, grid.RasterXSize))

    gdal.ReprojectImage(raw, grid, sourcePrj.ExportToWkt(), targetPrj.ExportToWkt(), gdal.GRA_NearestNeighbour,
                        options=['NUM_THREADS=ALL_CPUS'])

    raw = None

    # Read grid data
    array = grid.ReadAsArray()

    # Mask fill values (i.e. invalid values)
    np.ma.masked_where(array, array == -1, False)

    # Apply scale and offset
    array = array * self.scale + self.offset

    grid.GetRasterBand(1).SetNoDataValue(-1)
    grid.GetRasterBand(1).WriteArray(array)

    return grid