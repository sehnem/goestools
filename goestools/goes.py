from datetime import datetime
from filehandler import list_files
from download import get_goes
from reader import abi
from pyspectral.rayleigh import Rayleigh
from copy import deepcopy
import numpy as np
from pyorbital.astronomy import get_alt_az, sun_zenith_angle
from pyorbital.orbital import get_observer_look

regions = {'F': 'Fulldisk',
           'C': 'CONUS',
           'M1': 'Mesoscale 1',
           'M2': 'Mesoscale 2'}

products = {'Rad': 'Radiances',
            'CMIP': 'Cloud and Moisture Imagery products',
            'MCMIP': 'Multichannel Cloud and Moisture Imagery products'}

abi_bands = {'C01':1,'C02': 2,'C03': 3,'C04': 4,'C05': 5,'C06': 6,'C07': 7,
             'C08': 8,'C09': 9,'C10': 10,'C11': 11,'C12': 12, 'C13': 13,
             'C14': 14, 'C15': 15, 'C16': 16}

def simulated_green(c01, c02, c03):
    # Kaba:
    # return (c01 + c02) * 0.45 + 0.1 * c03
    # EDC:
    # return c01 * 0.45706946 + c02 * 0.48358168 + 0.06038137 * c03
    # Original:
    return (c01 + c02) / 2 * 0.93 + 0.07 * c03


class goes():

    def __init__(self, goes, product, region, date, bands=None, path='./', extent=None, local=False):
        #super(abi, self).__init__()
        #self.__dict__ = self

        if local is False:
            get_goes(goes, product, region, start=date, end=None, bands=bands, path=path)
        if type(date) is str:
            date = datetime.strptime(date, '%Y%m%d%H%M')
        self.files = list_files(path, bands, date)
        self.abi = []
        for file in self.files:
            data = abi(file, extent)
            self.__dict__['C'+str(data.band).zfill(2)] = data
            self.abi.append(self.__dict__['C'+str(data.band).zfill(2)])
        self.channels = [b for b in list(self.__dict__.keys()) if b in abi_bands.keys()]


    def calibrate(self):
        for ch in self.channels:
            getattr(self, ch).calibrate()


    def rgb_truecolor(self):
        self.calibrate()

        r = self.get_rayleightcorrected('C02', self.C02.data.data)
        #low_res_red = self.C02.four_elements_avg().data
        new_shape = (int(r.shape[0] / 2), 2, int(r.shape[1] / 2), 2)
        low_res_red = r
        low_res_red = np.ma.mean(low_res_red.reshape(new_shape), axis=(1, 3))

        b = self.get_rayleightcorrected('C01', low_res_red)
        #c03 = self.get_rayleightcorrected('C03', low_res_red)
        c03 = self.C03.data.data
        b = np.repeat(np.repeat(b, 2, axis=0), 2, axis=1)
        c03 = np.repeat(np.repeat(c03, 2, axis=0), 2, axis=1)
        g = simulated_green(b, r, c03)
        del c03

        #ratio = r / low_res_red

        #g *= ratio
        #b *= ratio


        rgb = np.stack([r, g, b], axis=2)
        rgb = np.maximum(rgb, 0.0)
        rgb = np.minimum(rgb, 1.0)
        #rgb = np.sqrt(rgb)

        self.RGB = deepcopy(self.C01)
        self.RGB.data = rgb
        self.RGB.product = 'Truecolor RGB'
        #del self.RGB.filename, self.RGB.band, self.RGB.wl_range, self.RGB.wl


    def get_rayleightcorrected(self, ch, r):

        row, col = self.__dict__[ch].data.shape
        cols = np.tile(np.arange(col), (row, 1))
        rows = np.tile(np.arange(row), (col, 1)).transpose()
        lons = self.__dict__[ch].afine['a'] * cols + self.__dict__[ch].afine['b'] * rows + self.__dict__[ch].afine['a'] * 0.5 + self.__dict__[ch].afine[
            'b'] * 0.5 + self.__dict__[ch].afine['c']
        lats = self.__dict__[ch].afine['d'] * cols + self.__dict__[ch].afine['e'] * rows + self.__dict__[ch].afine['d'] * 0.5 + self.__dict__[ch].afine[
            'e'] * 0.5 + self.C01.afine['f']

        sunalt, suna = get_alt_az(self.__dict__[ch].start, lons, lats)
        suna = np.rad2deg(suna)
        sunz = sun_zenith_angle(self.__dict__[ch].start, lons, lats)
        sata, satel = get_observer_look(self.__dict__[ch].info['satellite_longitude'],
                                        self.__dict__[ch].info['satellite_latitude'],
                                        self.__dict__[ch].info['satellite_altitude'],
                                        self.__dict__[ch].start, lons, lats, 0)
        satz = 90 - satel
        del satel

        sata = np.mod(sata, 360.)
        suna = np.mod(suna, 360.)
        ssadiff = np.abs(suna - sata)
        ssadiff = np.where(ssadiff > 180, 360 - ssadiff, ssadiff)
        del sata, suna

        corrector = Rayleigh('GOES-16', 'abi')#, atmosphere='us-standard', aerosol_type='marine_clean_aerosol') #atmosphere=atmosphere, aerosol_type=aerosol_type)
        correction = corrector.get_reflectance(sunz, satz, ssadiff, 'ch' + str(self.__dict__[ch].band), r)
        #correction = np.ma.masked_where(np.ma.getmask(self.__dict__[ch].data), correction)

        return self.__dict__[ch].data - correction/100
