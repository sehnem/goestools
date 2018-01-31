import boto3
import botocore
from botocore import UNSIGNED
from botocore.client import Config
import glob
import os
from .filehandler import list_files

regions = {'F': 'Fulldisk',
           'C': 'CONUS',
           'M1': 'Mesoscale 1',
           'M2': 'Mesoscale 2'}

products = {'Rad': 'radiances',
            'CMIP': 'Cloud and Moisture Imagery products',
            'MCMIP': 'Multichannel Cloud and Moisture Imagery products'}


# Goes class to process single time data, multiband capable.

class goes():

    def __init__(self, path, date,bands=None, local=False):
        files = list_files(path, bands, date)
        # verifica diretorio local e filtra conforme parâmetros
        # se não é local=True verifica diretorio remoto pela data e bandas
        # se existe data mais proxima no remoto baixa ela
        # revê diretório local para carregar o arquivo
        # chama o reader
