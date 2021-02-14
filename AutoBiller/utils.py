# -*- coding: utf-8 -*-

import csv, os, json

def get_download_path():
    """Returns the default downloads path for linux or windows"""
    if os.name == 'nt':
        import winreg
        sub_key = r'SOFTWARE\Microsoft\Windows\CurrentVersion\Explorer\Shell Folders'
        downloads_guid = '{374DE290-123F-4565-9164-39C4925E467B}'
        with winreg.OpenKey(winreg.HKEY_CURRENT_USER, sub_key) as key:
            location = winreg.QueryValueEx(key, downloads_guid)[0]
        return location
    else:
        return os.path.join(os.path.expanduser('~'), 'downloads')

def download_csv_file(filename, fieldnames, list_of_rows):
    """Writes a csv file to the given filename"""
    dir_name = get_download_path()
    path = dir_name + "/" + filename + ".csv"

    with open(path, mode='w+') as csv_file:

        writer = csv.DictWriter(csv_file, fieldnames=fieldnames)
        writer.writeheader()

        for row in list_of_rows:
            writer.writerow(row)

# fee_by_cpt_code = {
#     "90791": 550, #Initial Session
#     "96152": 120, #15 min
#     "90832": 200, #30 min
#     "90834": 280, #45 min
#     "90837": 350, #1 hr
#     "90853": 225, #Group
#     "90847": 400, #Couples
#     "90839": 500  #Crisis
# }

with open("resources/fees.json", "r") as f:
    fee_by_cpt_code = json.load(f)

def write_fees(new_fees):
    with open("resources/fees.json", "w+") as f:
        json.dump(new_fees, f)
