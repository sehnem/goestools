import os
import sys
import time
import boto3
import botocore
import threading
from datetime import datetime, timedelta
from boto3.s3.transfer import S3Transfer
from botocore.client import Config
from botocore import UNSIGNED

regions = {'F': 'Fulldisk',
           'C': 'CONUS',
           'M1': 'Mesoscale 1',
           'M2': 'Mesoscale 2'}

products = {'Rad': 'ABI-L1b-Rad',
            'CMIP': 'ABI-L2-CMIPF',
            'MCMIP': 'ABI-L2-MCMIPF'}


def parse_dates(date1, date2):
    if type(date1) is str:
        date1 = datetime.strptime(date1, '%Y%m%d%H%M')
    if type(date1) is str:
        date2 = datetime.strptime(date2, '%Y%m%d%H%M')
    return date1, date2


def list_dir(bucket, client, prefix=''):
    out = {'dir': [], 'file': []}
    ls = client.list_objects_v2(Bucket=bucket, Prefix=prefix, Delimiter='/')
    if 'CommonPrefixes' in ls:
        for o in ls.get('CommonPrefixes'):
            out['dir'].append(o.get('Prefix'))
    if 'Contents' in ls:
        for file in ls.get('Contents'):
            out['file'].append(file)
    return out


def date_to_prefix(product, dates):
    prefixes = []
    for date in dates:
        prefix = date.strftime(product+'/%Y/%j/%H/')
        if prefix not in prefixes:
            prefixes.append(prefix)
    return prefixes


def last_archive(bucket, client, prefix, depth, ftype='file'):
    dates = []
    rfiles = []
    for x in range(depth-1):
        prefix = list_dir(bucket, client, prefix)['dir'][-1]
    files = list_dir(bucket, client, prefix)[ftype]
    for file in files:
        datev = datetime.strptime(file['Key'][52:-36], '%Y%j%H%M%S')
        dates.append(time.mktime(datev.timetuple()))
    c_date = max(dates)
    stamp = datetime.fromtimestamp(c_date).strftime('%Y%j%H%M%S')
    for file in files:
        if file['Key'][52:-36] == stamp:
            rfiles.append(file)
    return rfiles


def closest_date(files, date):
    dates = []
    rfiles = []
    date = time.mktime(date.timetuple())
    for file in files:
        datev = datetime.strptime(file['Key'][52:-36], '%Y%j%H%M%S')
        dates.append(time.mktime(datev.timetuple()))
    c_date = min(dates, key=lambda x: abs(x-date))
    stamp = datetime.fromtimestamp(c_date).strftime('%Y%j%H%M%S')
    for file in files:
        if file['Key'][52:-36] == stamp:
            rfiles.append(file)
    return rfiles


def band_filter(files, bands):
    if bands is None:
        return files
    else:
        if type(bands) is int:
            bands = [bands]
    drop = []
    for i, file in enumerate(files):
        band = int(files[i]['Key'][44:46])
        if band not in bands:
            drop.append(i)
    for index in sorted(drop, reverse=True):
        del files[index]
    return files


def date_filter(files, start, end):
    drop = []
    for i, file in enumerate(files):
        date = datetime.strptime(file['Key'][52:-36], '%Y%j%H%M%S')
        if date <= start or date >= end:
            drop.append(i)
    for index in sorted(drop, reverse=True):
        del files[index]
    return files


class ProgressPercentage(object):
    def __init__(self, filename, size):
        self._filename = filename
        self._size = size
        self._seen_so_far = 0
        self._lock = threading.Lock()

    def __call__(self, bytes_amount):
        with self._lock:
            self._seen_so_far += bytes_amount
            bl, status = 50, ""
            progress = (self._seen_so_far / self._size)
            if progress >= 1.:
                progress, status = 1, "\r"
            block = int(round(bl * progress))
            text = '\r[{}] {:.0f}% {}'.format('#' * block + '-' * (bl - block),
                                              round(progress * 100, 0), status)
            sys.stdout.write(text)
            sys.stdout.flush()


def get_goes(goes, product, region, start=None, end=None, bands=None, path='./'):

    bucket = 'noaa-goes' + str(goes)
    client = boto3.client('s3', config=Config(signature_version=UNSIGNED))

    start, end = parse_dates(start, end)

    product = products[product]
    regions[region]
    product = product + region

    files = []
    if end is None and start is None:
        files.extend(last_archive(bucket, client, product + '/', 4))

    else:
        if end is None:
            date = start
            dates = [date + timedelta(hours=x) for x in range(-1, 2)]
        else:
            days = (end - start).days + 1
            dates = [start + timedelta(days=x) for x in range(0, days)]
        prefixes = date_to_prefix(product, dates)
        for prefix in prefixes:
            try:
                files.extend(list_dir(bucket, client, prefix)['file'])
            except FileNotFoundError:
                print('Folder {} not found.'.format(prefix))
                continue
        if end is None:
            files = closest_date(files, date)
        else:
            files = date_filter(files, start, end)
    files = band_filter(files, bands)

    fm = '%Y%j%H%M%S'

    for file in files:
        filename = file['Key'].split('/')[-1]
        output = path + filename
        file['Filename'] = filename
        file['ScanStart'] = datetime.strptime(filename[-49:-36], fm)
        file['ScanEnd'] = datetime.strptime(filename[-33:-20], fm)
        file['FileCreation'] = datetime.strptime(filename[-17:-4], fm)
        file['Band'] = int(filename[-57:-55])

        if os.path.isfile(output):
            file['Local'] = True
        else:
            file['Local'] = False

    transfer = S3Transfer(client)
    for n, file in enumerate(files):
        output = path + file['Filename']
        if os.path.isfile(output):
            continue
        if file['StorageClass'] is not 'GLACIER':
            progress = ProgressPercentage(output, file['Size'])
            try:
                print('Downloading {}/{}'.format(n + 1, len(files)))
                print(file['Filename'])
                transfer.download_file(bucket, file['Key'], output,
                                       callback=progress)
            except botocore.exceptions.ClientError as e:
                if e.response['Error']['Code'] == "404":
                    print("The object does not exist.")
                else:
                    raise
        elif file['StorageClass'] is 'GLACIER':
            try:
                pass
            except NotImplementedError:
                print('Glacier retrieve not yet supported')
