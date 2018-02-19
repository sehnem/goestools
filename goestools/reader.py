from netCDF4 import Dataset
import numpy as np
from copy import deepcopy
from remap import remap

# https://www.goes-r.gov/spacesegment/images/ABI-tech-summary.png
abi_bands = {1:  {'wl_range': (0.45, 0.49),   'wl': 0.47,  'res': 1},
             2:  {'wl_range': (0.59, 0.69),   'wl': 0.64,  'res': 0.5},
             3:  {'wl_range': (0.846, 0.885), 'wl': 0.865, 'res': 1},
             4:  {'wl_range': (1.371, 1.386), 'wl': 1.378, 'res': 2},
             5:  {'wl_range': (1.58, 1.64),   'wl': 1.61,  'res': 1},
             6:  {'wl_range': (2.225, 2.275), 'wl': 2.25,  'res': 2},
             7:  {'wl_range': (3.80, 4.00),   'wl': 3.90,  'res': 2},
             8:  {'wl_range': (5.77, 6.6),    'wl': 6.19,  'res': 2},
             9:  {'wl_range': (6.75, 7.15),   'wl': 6.95,  'res': 2},
             10: {'wl_range': (7.24, 7.44),   'wl': 7.34,  'res': 2},
             11: {'wl_range': (8.3, 8.7),     'wl': 8.5,   'res': 2},
             12: {'wl_range': (9.42, 9.8),    'wl': 9.61,  'res': 2},
             13: {'wl_range': (10.1, 10.6),   'wl': 10.35, 'res': 2},
             14: {'wl_range': (10.8, 11.6),   'wl': 11.2,  'res': 2},
             15: {'wl_range': (11.8, 12.8),   'wl': 12.3,  'res': 2},
             16: {'wl_range': (13.0, 13.6),   'wl': 13.3,  'res': 2}}


class abi(dict):

    def __init__(self, file, extent=None):
        super(abi, self).__init__()
        self.__dict__ = self

        nc = Dataset(file['filename'], 'r')
        self.filename = file['filename']
        if file['product']=='CMIP':
            self.product = 'CMI'
        else:
            self.product = file['product']
        self.band = file['band']
        self.goes = file['goes_satellite']
        self.start = file['start']
        self.end = file['end']
        self.wl_range = abi_bands[self.band]['wl_range']
        self.wl = abi_bands[self.band]['wl']
        self.resolution = abi_bands[self.band]['res']
        self.rows, self.cols = nc[self.product].shape

        if self.band < 7:
            self.solar_irradiance = nc['esun'][0]
            self.esd = nc["earth_sun_distance_anomaly_in_AU"][0]
        else:
            self.fk1 = nc["planck_fk1"][0]
            self.fk2 = nc["planck_fk2"][0]
            self.bc1 = nc["planck_bc1"][0]
            self.bc2 = nc["planck_bc2"][0]


        self.info = {'satellite_latitude': nc['nominal_satellite_subpoint_lat'][0],
                     'satellite_longitude': nc['nominal_satellite_subpoint_lon'][0],
                     'satellite_altitude': nc['nominal_satellite_height'][0]}

        projection = nc["goes_imager_projection"]
        a = projection.semi_major_axis
        h = projection.perspective_point_height
        b = projection.semi_minor_axis
        lon_0 = projection.longitude_of_projection_origin
        sweep_axis = projection.sweep_angle_axis


        variable = nc[self.product]
        if self.product=='Rad':
            self.data = (np.ma.masked_equal(variable, variable._FillValue, copy=False) * variable.scale_factor + variable.add_offset)
        else:
            self.data = np.ma.masked_equal(variable, variable._FillValue, copy=False)


        scale_x = np.float64(nc['x'].scale_factor)
        scale_y = np.float64(nc['y'].scale_factor)
        offset_x = np.float64(nc['x'].add_offset)
        offset_y = np.float64(nc['y'].add_offset)

        x_l = h * (nc['x'][0] * scale_x + offset_x)
        x_r = h * (nc['x'][-1] * scale_x + offset_x)
        y_l = h * (nc['y'][-1] * scale_y + offset_y)
        y_u = h * (nc['y'][0] * scale_y + offset_y)
        x_half = (x_r - x_l) / (self.cols - 1) / 2.
        y_half = (y_u - y_l) / (self.rows - 1) / 2.
        self.extent = (x_l - x_half, x_r + x_half, y_l - y_half, y_u + y_half)

        self.area = {'proj': 'geos',
                     'a': float(a),
                     'b': float(b),
                     'lat_0': 0.0,
                     'lon_0': float(lon_0),
                     'h': h,
                     'units': 'm',
                     'sweep': sweep_axis,
                     'no_defs': ''}

        if extent is not None:
            self.reproj(extent=extent)


    def calibrate(self):

        if self.product=='Rad' and self.band < 7:
            factor = np.pi * self.esd * self.esd / self.solar_irradiance
            self.data *= factor
            self.product = 'CMI'

        elif self.product=='Rad':
            np.divide(self.fk1, self.data, out=self.data)
            self.data.data[:] += 1
            np.log(self.data, out=self.data)
            np.divide(self.fk2, self.data, out=self.data)
            self.data[:] -= self.bc1
            self.data[:] /= self.bc2
            self.product = 'CMI'


    def reproj(self, extent):
        remap(self, extent)


    def four_elements_avg(self):
        data = deepcopy(self)
        data.__dict__ = self.__dict__.copy()
        new_shape = (int(data.rows / 2), 2, int(data.cols / 2), 2)
        data.data = np.ma.mean(data.data.reshape(new_shape), axis=(1, 3))
        data.rows, data.cols = data.data.shape
        return data
