import boto3
import botocore
from botocore import UNSIGNED
from botocore.client import Config
import glob
import os
from .filehandler import list_files
from .download import get_goes
from .reader import abi

regions = {'F': 'Fulldisk',
           'C': 'CONUS',
           'M1': 'Mesoscale 1',
           'M2': 'Mesoscale 2'}

products = {'Rad': 'Radiances',
            'CMIP': 'Cloud and Moisture Imagery products',
            'MCMIP': 'Multichannel Cloud and Moisture Imagery products'}

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


class goes():

    def __init__(self, goes, product, region, date, bands=None, path='./', local=False):
        if local is False:
            get_goes(goes, product, region, start=date, end=None, bands=None, path=path)
        files = list_files(path, bands, date)
        data = []
        for file in files:
            data.append(abi(file))
# criar dicionário com as bandas
#carregar de cada banda que existe neste dicionário

# chama o reader
