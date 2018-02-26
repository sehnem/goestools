from netCDF4 import Dataset
import numpy as np
from osgeo import osr
from osgeo import gdal
from osgeo import gdal_array
import time as t

def area_string(dict):
    area = ''
    for value in list(dict.keys()):
        if str(dict[value]) is not '':
            param = '+' + value + '=' + str(dict[value]) + ' '
        else:
            param = '+' + value + ' '
        area += param
    return area[:-1]

def area_dict(string):
    areadict={}
    for value in string.split(' '):
        value = value.split('=')
        if len(value) > 1:
            areadict[value[0][1:]] = value[1]
        else:
            areadict[value[0][1:]] = ''
    return areadict

# TODO: Reescrever metadados da nova projeção

# Define KM_PER_DEGREE
KM_PER_DEGREE = 111.32

# nc.variables['goes_imager_projection']

# GOES-16 Extent (satellite projection) [llx, lly, urx, ury]
# GOES16_EXTENT = [-5434894.885056, -5434894.885056, 5434894.885056, 5434894.885056]
# GOES16_EXTENT = [-5434546.127484, 5434546.127484, -5434241.773362, 5434241.773362]


def getGeoT(extent, nrows, ncols):
    # Compute resolution based on data dimension
    resx = (extent[2] - extent[0]) / ncols
    resy = (extent[3] - extent[1]) / nrows
    return [extent[0], resx, 0, extent[3], 0, -resy]


def remap(self, extent, t_area={'datum': 'WGS84', 'ellps': 'WGS84', 'proj': 'longlat', 'no_defs': ''}):
    area_dest = area_string(t_area)
    area_def = area_string(self.area)
    sourcePrj = osr.SpatialReference()
    sourcePrj.ImportFromProj4(area_def)

    targetPrj = osr.SpatialReference()
    targetPrj.ImportFromProj4(area_dest)

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

    gdal.ReprojectImage(raw, grid, sourcePrj.ExportToWkt(), targetPrj.ExportToWkt(), gdal.GRA_NearestNeighbour, options=['NUM_THREADS=ALL_CPUS']) #gdal.GRA_Bilinear,

    # Close file
    del raw

    # Read grid data
    array = grid.ReadAsArray()
    np.ma.masked_where(array, array == -1, False)

    grid.GetRasterBand(1).SetNoDataValue(-1)
    grid.GetRasterBand(1).WriteArray(array)
    array = np.ma.masked_equal(grid.ReadAsArray(), array == -1, False)

    c, a, b, f, d, e = grid.GetGeoTransform()
    self.afine = {'c':c, 'a':a, 'b':b, 'f':f, 'd':d, 'e':e}
    self.rows, self.cols = array.shape
    self.extent = extent
    self.area = t_area
    self.data = array