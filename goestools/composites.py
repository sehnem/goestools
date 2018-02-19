import goes
import numpy as np
from copy import deepcopy






def rgb_truecolor(self):
    self.calibrate()
    r = deepcopy(self.C02.data)
    b = deepcopy(self.C01.data)
    low_res_red = self.C02.four_element_average(r)
    b = rayleighcorrection(self, b, low_res_red)
    c03 = deepcopy(self.C03.data)
    b = np.repeat(np.repeat(b, 2, axis=0), 2, axis=1)
    c03 = np.repeat(np.repeat(c03, 2, axis=0), 2, axis=1)
    g = simulated_green(b, r, c03)
    del c03

    low_res_red = np.repeat(np.repeat(low_res_red, 2, axis=0), 2, axis=1)
    ratio = r / low_res_red

    g *= ratio
    b *= ratio


def rayleighcorrection(self, vis, red):

    if vis.shape != red.shape:
        print('IncompatibleAreas')
    row, col = vis.shape
    cols = np.tile(np.arange(col),(row,1))
    rows = np.tile(np.arange(row),(col,1)).transpose()
    lons = self.C01.afine['a'] * cols + self.C01.afine['b'] * rows + self.C01.afine['a'] * 0.5 + self.C01.afine['b'] * 0.5 + self.C01.afine['c']
    lats = self.C01.afine['d'] * cols + self.C01.afine['e'] * rows + self.C01.afine['d'] * 0.5 + self.C01.afine['e'] * 0.5 + self.C01.afine['f']

    sunalt, suna = get_alt_az(self.C01.start, lons, lats)
    suna = np.rad2deg(suna)
    sunz = sun_zenith_angle(self.C01.start, lons, lats)
    sata, satel = get_observer_look(self.C01.area['lon_0'], self.C01.area['lat_0'], self.C01.area['h'], self.C01.start, lons, lats, 0)
    satz = 90 - satel
    del satel

    sata = np.mod(sata, 360.)
    suna = np.mod(suna, 360.)
    ssadiff = np.abs(suna - sata)
    ssadiff = np.where(ssadiff > 180, 360 - ssadiff, ssadiff)
    del sata, suna

    atmosphere = self.info.get('atmosphere', 'us-standard')
    aerosol_type = self.info.get('aerosol_type', 'marine_clean_aerosol')

    corrector = Rayleigh('GOES-16', 'abi', atmosphere=atmosphere, aerosol_type=aerosol_type)
    return corrector.get_reflectance(sunz, satz, ssadiff, vis, red)
