from netCDF4 import Dataset
import numpy as np


class abi():

    def __init__(self, file):
        self.nc = Dataset(file['filename'], 'r')
        self.var = file['product']
        self.band = file['band']
        self.goes = file['goes_satellite']
        self.start = file['start']
        self.end = file['end']
        self.nlines, self.ncols = self.nc[self.var].shape

        variable = self.nc[self.var]
        radiances = (np.ma.masked_equal(variable, variable._FillValue, copy=False) * variable.scale_factor + variable.add_offset)

        data = []
        mask = []
        data[:] = radiances
        mask[:] = np.ma.getmask(radiances)
        info = {'satellite_latitude': self.nc['nominal_satellite_subpoint_lat'][()],
                'satellite_longitude': self.nc['nominal_satellite_subpoint_lon'][()],
                'satellite_altitude': self.nc['nominal_satellite_height'][()]}

        projection = self.nc["goes_imager_projection"]
        a = projection.semi_major_axis
        h = projection.perspective_point_height
        b = projection.semi_minor_axis
        lon_0 = projection.longitude_of_projection_origin
        sweep_axis = projection.sweep_angle_axis

        # need 64-bit floats otherwise small shift
        scale_x = np.float64(self.nc['x'].scale_factor)
        scale_y = np.float64(self.nc['y'].scale_factor)
        offset_x = np.float64(self.nc['x'].add_offset)
        offset_y = np.float64(self.nc['y'].add_offset)

        # x and y extents in m
        x_l = h * (self.nc['x'][0] * scale_x + offset_x)
        x_r = h * (self.nc['x'][-1] * scale_x + offset_x)
        y_l = h * (self.nc['y'][-1] * scale_y + offset_y)
        y_u = h * (self.nc['y'][0] * scale_y + offset_y)
        x_half = (x_r - x_l) / (self.ncols - 1) / 2.
        y_half = (y_u - y_l) / (self.nlines - 1) / 2.
        area_extent = (x_l - x_half, y_l - y_half, x_r + x_half, y_u + y_half)

        proj_dict = {'a': float(a),
                     'b': float(b),
                     'lon_0': float(lon_0),
                     'h': h,
                     'proj': 'geos',
                     'units': 'm',
                     'sweep': sweep_axis,
                     'lines': self.nlines,
                     'cols': self.ncols,
                     'extent': area_extent}
