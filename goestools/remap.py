from netCDF4 import Dataset
import numpy as np
from osgeo import osr
from osgeo import gdal
from osgeo import gdal_array
import time as t

def area_string(dict):
    area = ''
    for value in list(dict.keys()):
        param = '+' + value + '=' + str(dict[value]) + ' '
        area += param
    area += '+no_defs'
    return area

# TODO: Reescrever metadados da nova projeção

# Define KM_PER_DEGREE
KM_PER_DEGREE = 111.32

# nc.variables['goes_imager_projection']

# GOES-16 Extent (satellite projection) [llx, lly, urx, ury]
# GOES16_EXTENT = [-5434894.885056, -5434894.885056, 5434894.885056, 5434894.885056]
# GOES16_EXTENT = [-5434546.127484, 5434546.127484, -5434241.773362, 5434241.773362]


def getGeoT(extent, nlines, ncols):
    # Compute resolution based on data dimension
    resx = (extent[2] - extent[0]) / ncols
    resy = (extent[3] - extent[1]) / nlines
    return [extent[0], resx, 0, extent[3], 0, -resy]


def remap(self, extent):

    area_def = area_string(self.area)
    sourcePrj = osr.SpatialReference()
    sourcePrj.ImportFromProj4(area_def)

    targetPrj = osr.SpatialReference()
    targetPrj.ImportFromProj4('+proj=longlat +ellps=WGS84 +datum=WGS84 +no_defs')

    raw = gdal_array.OpenArray(self.data)

    # Setup projection and geo-transformation
    raw.SetProjection(sourcePrj.ExportToWkt())
    raw.SetGeoTransform(getGeoT(self.extent, raw.RasterYSize, raw.RasterXSize))

    # Compute grid dimension
    sizex = int((extent[2] - extent[0]) * KM_PER_DEGREE/2) * int(2/self.resolution)
    sizey = int((extent[3] - extent[1]) * KM_PER_DEGREE/2) * int(2/self.resolution)

    # Get memory driver
    memDriver = gdal.GetDriverByName('MEM')

    # Create grid
    grid = memDriver.Create('grid', sizex, sizey, 1, gdal.GDT_Float32)

    # Setup projection and geo-transformation
    grid.SetProjection(targetPrj.ExportToWkt())
    grid.SetGeoTransform(getGeoT(extent, grid.RasterYSize, grid.RasterXSize))

    gdal.ReprojectImage(raw, grid, sourcePrj.ExportToWkt(), targetPrj.ExportToWkt(), gdal.GRA_NearestNeighbour,
                        options=['NUM_THREADS=ALL_CPUS'])

    # Close file
    del raw

    # Read grid data
    array = grid.ReadAsArray()

    # Mask fill values (i.e. invalid values)
    np.ma.masked_where(array, array == -1, False)


    grid.GetRasterBand(1).SetNoDataValue(-1)
    grid.GetRasterBand(1).WriteArray(array)

    array = np.ma.masked_equal(grid.ReadAsArray(), array == -1, False)

    self.data = array