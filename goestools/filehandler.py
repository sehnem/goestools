import time
from glob import glob
from datetime import datetime


def file_to_dict(file_name):
    """
    :param file_name: name of the file
    :return: dictionary of metadata from goes filename
    """

    goes_dict = {}
    fmt = '%Y%j%H%M%S%f'

    name_data = file_name[:-3].split('_')
    product = name_data[1].split('-')

    goes_dict['goes_satellite'] = int(name_data[2][1:])
    goes_dict['start'] = datetime.strptime(name_data[3][1:], fmt)
    goes_dict['end'] = datetime.strptime(name_data[4][1:], fmt)
    goes_dict['created'] = datetime.strptime(name_data[5][1:], fmt)
    goes_dict['instrument'] = product[0]
    goes_dict['process_level'] = product[1]
    goes_dict['mode'] = product[3][1]

    split_p = 2 if product[2][-2] is 'M' else 1

    goes_dict['region'] = product[2][-split_p:]
    goes_dict['product'] = product[2][:-split_p]

    if goes_dict['product'] is 'MCMIP':
        goes_dict['band'] = list(range(17))
    else:
        goes_dict['band'] = int(product[3][-2:])

    return goes_dict


def list_files(path, bands, date=None):
    """
    Parse local files to find the wanted ones
    :param path:
    :param bands:
    :param date:
    :return:
    """

    bands = list(range(17)) if bands is None else bands

    files = glob(path + '/OR_ABI-*.nc')
    files = [file_to_dict(file) for file in files]

    files = [file for file in files if file['band'] in bands] #band filter

    if date is not None:
        dates = [file['start'] for file in files] # get start scan dates
        dates = list(set(dates)) #remove duplicated
        diff = [abs((dt-date).total_seconds()) for dt in dates] # calculate de difference
        min_idx = diff.index(min(diff))
        date = [dates[min_idx]]
        files = [file for file in files if file['start'] in date]  # date filter

    return files
