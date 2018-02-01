import logging
import os
from datetime import datetime

from netCDF4 import Dataset
import numpy as np



class NC_ABI_L1B(BaseFileHandler):

    def __init__(self, filename, filename_info, filetype_info):
        super(NC_ABI_L1B, self).__init__(filename, filename_info,
                                         filetype_info)
        self.nc = Dataset(filename, 'r')

        platform_shortname = filename_info['platform_shortname']
        self.platform_name = PLATFORM_NAMES.get(platform_shortname)
        self.sensor = 'abi'
        self.nlines, self.ncols = self.nc["Rad"].shape

    def get_shape(self, key, info):
        """Get the shape of the data."""
        return self.nlines, self.ncols

    def get_dataset(self, key, info, out=None,
                    xslice=slice(None), yslice=slice(None)):
        """Load a dataset."""
        logger.debug('Reading in get_dataset %s.', key.name)

        variable = self.nc["Rad"]

        radiances = (np.ma.masked_equal(variable[yslice, xslice],
                                        variable._FillValue, copy=False) *
                     variable.scale_factor +
                     variable.add_offset)
        # units = variable.attrs['units']
        units = self.calibrate(radiances)

        # convert to satpy standard units
        if units == '1':
            radiances.data[:] *= 100.
            units = '%'

        out.data[:] = radiances
        out.mask[:] = np.ma.getmask(radiances)
        out.info.update({'units': units,
                         'platform_name': self.platform_name,
                         'sensor': self.sensor,
                         'satellite_latitude': self.nc['nominal_satellite_subpoint_lat'][()],
                         'satellite_longitude': self.nc['nominal_satellite_subpoint_lon'][()],
                         'satellite_altitude': self.nc['nominal_satellite_height'][()]})
        out.info.update(key.to_dict())

        return out

    def get_area_def(self, key):
        """Get the area definition of the data at hand."""
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
                     'sweep': sweep_axis}

# TODO: create dict
        area = geometry.AreaDefinition(
            'some_area_name',
            "On-the-fly area",
            'geosabii',
            proj_dict,
            self.ncols,
            self.nlines,
            area_extent)

        return area

    def _vis_calibrate(self, data):
        """Calibrate visible channels to reflectance."""
        solar_irradiance = self.nc['esun'][()]
        esd = self.nc["earth_sun_distance_anomaly_in_AU"][()]

        factor = np.pi * esd * esd / solar_irradiance
        data.data[:] *= factor

        return '1'

    def _ir_calibrate(self, data):
        """Calibrate IR channels to BT."""
        fk1 = self.nc["planck_fk1"][()]
        fk2 = self.nc["planck_fk2"][()]
        bc1 = self.nc["planck_bc1"][()]
        bc2 = self.nc["planck_bc2"][()]

        np.divide(fk1, data, out=data.data)
        data.data[:] += 1
        np.log(data, out=data.data)
        np.divide(fk2, data, out=data.data)
        data.data[:] -= bc1
        data.data[:] /= bc2

        return 'K'

    def calibrate(self, data):
        """Calibrate the data."""
        logger.debug("Calibrate")

        ch = self.nc["band_id"][()]
        if ch < 7:
            return self._vis_calibrate(data)
        else:
            return self._ir_calibrate(data)

    @property
    def start_time(self):
        return datetime.strptime(self.nc.time_coverage_start, '%Y-%m-%dT%H:%M:%S.%fZ')

    @property
    def end_time(self):
        return datetime.strptime(self.nc.time_coverage_end, '%Y-%m-%dT%H:%M:%S.%fZ')