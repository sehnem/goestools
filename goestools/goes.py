import boto3
import botocore
from datetime import datetime
from botocore import UNSIGNED
from botocore.client import Config
import glob
import os
from filehandler import list_files
from download import get_goes
from reader import abi

regions = {'F': 'Fulldisk',
           'C': 'CONUS',
           'M1': 'Mesoscale 1',
           'M2': 'Mesoscale 2'}

products = {'Rad': 'Radiances',
            'CMIP': 'Cloud and Moisture Imagery products',
            'MCMIP': 'Multichannel Cloud and Moisture Imagery products'}


class goes():

    def __init__(self, goes, product, region, date, bands=None, path='./', local=False):
        if local is False:
            get_goes(goes, product, region, start=date, end=None, bands=bands, path=path)
        if type(date) is str:
            date = datetime.strptime(date, '%Y%m%d%H%M')
        self.files = list_files(path, bands, date)
        self.abi = []
        for file in self.files:
            self.abi.append(abi(file))
# criar dicionário com as bandas
#carregar de cada banda que existe neste dicionário

# chama o reader
