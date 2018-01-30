import boto3
import botocore
from botocore import UNSIGNED
from botocore.client import Config
import glob
import os

regions = {'F': 'Fulldisk',
           'C': 'CONUS',
           'M1': 'Mesoscale 1',
           'M2': 'Mesoscale 2'}

products = {'Rad': 'radiances',
            'CMIP': 'Cloud and Moisture Imagery products',
            'MCMIP': 'Multichannel Cloud and Moisture Imagery products'}


# Goes class to process single time data, multiband capable.

class goes():

    def __init__(self, path, local=True):
        files = glob('path/OR_ABI*G*.nc')
