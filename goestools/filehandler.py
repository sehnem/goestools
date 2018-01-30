from datetime import datetime


def file_name_parser(file_name):
    """
    :param file_name: name of the file
    :return: dictionary of metadata from goes filename
    """

    goes_file = {}
    fmt = '%Y%j%H%M%S%f'

    name_data = file_name[:-3].split('_')
    product = name_data[1].split('-')

    goes_file['goes_satellite'] = int(name_data[2][1:])
    goes_file['start'] = datetime.strptime(name_data[3][1:], fmt)
    goes_file['end'] = datetime.strptime(name_data[4][1:], fmt)
    goes_file['created'] = datetime.strptime(name_data[5][1:], fmt)
    goes_file['instrument'] = product[0]
    goes_file['process_level'] = product[1]
    goes_file['mode'] = product[3][1]

    split_p = 2 if product[2][-2] is 'M' else 1

    goes_file['region'] = product[2][-split_p:]
    goes_file['product'] = product[2][:-split_p]

    if goes_file['product'] is 'MCMIP':
        goes_file['band'] = list(range(17))
    else:
        goes_file['band'] = int(product[3][-2:])

    return goes_file
