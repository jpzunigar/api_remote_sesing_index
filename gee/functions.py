from datetime import datetime, timedelta
from datetime import date
import rasterio
import os
import errno


class GeneralFunctions:
    def get_list_dates():
        start_date = datetime(2020, 1, 1)
        end_date = datetime.now()
        date_list = []
        current_date = start_date
        while current_date <= end_date:
            date_list.append(current_date.strftime('%Y-%m-%d'))
            current_date += timedelta(days=1)
        return date_list

    def create_path(path):
        try:
            os.mkdir(path)
        except OSError as e:
            if e.errno != errno.EEXIST:
                raise

    def save_index(json_data_img):
        with rasterio.open(
            os.path.join('static', 'temp', json_data_img['Name_TimeStap']),
            'w',
            driver='GTiff',
            height=json_data_img['height'],
            width=json_data_img['width'],
            count=1,
            dtype=json_data_img['dtype'],
            crs=json_data_img['crs'],
            transform=json_data_img['transform'],
            nodata=json_data_img['NoData'],
        ) as dst:
            dst.write(json_data_img['index'], 1)
        return os.path.join('temp', json_data_img['Name_TimeStap'])
