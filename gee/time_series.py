import ee
from gee.gee_utils import GeeUtils
from ee import ImageCollection
from ee import Filter
from datetime import date
import pandas as pd


class TimeSeries:
    # ee.Initialize()
    def ts_ndvi(fc):
        """Función que obtiene mapa de folium con índice de vegetación de diferencia normalizada

        Args:

        Returns:
            [Json]:
        """
        today = date.today()
        date_today = today.strftime('%Y-%m-%d')

        s2_collection = ImageCollection('COPERNICUS/S2_SR_HARMONIZED').filterDate('2022-01-01', date_today)\
            .filterBounds(fc).filter(Filter.lte('CLOUDY_PIXEL_PERCENTAGE', 60))
        s2_collection = s2_collection.map(GeeUtils.indexNDVI_ts)

        def aoi_mean(img):

            mean = img.reduceRegion(
                reducer=ee.Reducer.mean(), geometry=fc, scale=10).get('NDVI')
            return img.set('date', img.date().format()).set('mean', mean)
        collection_reduced = s2_collection.map(aoi_mean)
        nested_list = collection_reduced.reduceColumns(
            ee.Reducer.toList(2), ['date', 'mean']).values().get(0)
        df = pd.DataFrame(nested_list.getInfo(), columns=['date', 'mean'])
        df['date'] = pd.to_datetime(df['date']).dt.strftime('%Y-%m-%d')
        df = df.groupby(['date']).mean()
        df = df.reset_index()
        df['mean'] = df['mean'].astype(float).round(2)
        dates_ts = list(df['date'])
        mean_ts = list(df['mean'])
        dict_ts = {'dates': dates_ts, 'mean_ts': mean_ts}
        return dict_ts

    def ts_evi(fc):
        """Función que obtiene mapa de folium con índice de vegetación de diferencia normalizada

        Args:

        Returns:
            [Json]:
        """
        today = date.today()
        date_today = today.strftime('%Y-%m-%d')

        s2_collection = ImageCollection('COPERNICUS/S2_SR_HARMONIZED').filterDate('2022-01-01', date_today)\
            .filterBounds(fc).filter(Filter.lte('CLOUDY_PIXEL_PERCENTAGE', 60))
        s2_collection = s2_collection.map(GeeUtils.IndexEVI_ts)

        def aoi_mean(img):
            try:
                mean = img.reduceRegion(
                    reducer=ee.Reducer.mean(), geometry=fc, scale=10).get('EVI')
            except:
                pass
            return img.set('date', img.date().format()).set('mean', mean)

        collection_reduced = s2_collection.map(aoi_mean)
        nested_list = collection_reduced.reduceColumns(
            ee.Reducer.toList(2), ['date', 'mean']).values().get(0)
        df = pd.DataFrame(nested_list.getInfo(), columns=['date', 'mean'])
        df['date'] = pd.to_datetime(df['date']).dt.strftime('%Y-%m-%d')
        df = df.groupby(['date']).mean()
        df = df.reset_index()
        df['mean'] = df['mean'].astype(float).round(2)
        df = df[df['mean'] > 0]
        df = df[df['mean'] < 1]
        dates_ts = list(df['date'])
        mean_ts = list(df['mean'])
        dict_ts = {'dates': dates_ts, 'mean_ts': mean_ts}
        return dict_ts

    def ts_ndmi(fc):
        """Función que obtiene mapa de folium con índice de vegetación de diferencia normalizada

        Args:

        Returns:
            [Json]:
        """
        today = date.today()
        date_today = today.strftime('%Y-%m-%d')

        s2_collection = ImageCollection('COPERNICUS/S2_SR_HARMONIZED').filterDate('2022-01-01', date_today)\
            .filterBounds(fc).filter(Filter.lte('CLOUDY_PIXEL_PERCENTAGE', 60))
        s2_collection = s2_collection.map(GeeUtils.indexNDMI)

        def aoi_mean(img):
            try:
                mean = img.reduceRegion(
                    reducer=ee.Reducer.mean(), geometry=fc, scale=10).get('NDMI')
            except:
                pass
            return img.set('date', img.date().format()).set('mean', mean)

        collection_reduced = s2_collection.map(aoi_mean)
        nested_list = collection_reduced.reduceColumns(
            ee.Reducer.toList(2), ['date', 'mean']).values().get(0)
        df = pd.DataFrame(nested_list.getInfo(), columns=['date', 'mean'])
        df['date'] = pd.to_datetime(df['date']).dt.strftime('%Y-%m-%d')
        df = df.groupby(['date']).mean()
        df = df.reset_index()
        df['mean'] = df['mean'].astype(float).round(2)
        dates_ts = list(df['date'])
        mean_ts = list(df['mean'])
        dict_ts = {'dates': dates_ts, 'mean_ts': mean_ts}
        return dict_ts

    def ts_cig(fc):
        """Función que obtiene mapa de folium con índice de vegetación de diferencia normalizada

        Args:

        Returns:
            [Json]:
        """
        today = date.today()
        date_today = today.strftime('%Y-%m-%d')

        s2_collection = ImageCollection('COPERNICUS/S2_SR_HARMONIZED').filterDate('2022-01-01', date_today)\
            .filterBounds(fc).filter(Filter.lte('CLOUDY_PIXEL_PERCENTAGE', 60))
        s2_collection = s2_collection.map(GeeUtils.indexCIG)

        def aoi_mean(img):
            try:
                mean = img.reduceRegion(
                    reducer=ee.Reducer.mean(), geometry=fc, scale=10).get('CIG')
            except:
                pass
            return img.set('date', img.date().format()).set('mean', mean)

        collection_reduced = s2_collection.map(aoi_mean)
        nested_list = collection_reduced.reduceColumns(
            ee.Reducer.toList(2), ['date', 'mean']).values().get(0)
        df = pd.DataFrame(nested_list.getInfo(), columns=['date', 'mean'])
        df['date'] = pd.to_datetime(df['date']).dt.strftime('%Y-%m-%d')
        df = df.groupby(['date']).mean()
        df = df.reset_index()
        df['mean'] = df['mean'].astype(float).round(2)
        dates_ts = list(df['date'])
        mean_ts = list(df['mean'])
        dict_ts = {'dates': dates_ts, 'mean_ts': mean_ts}
        return dict_ts

    def ts_sar_vv(fc):
        """Función que obtiene mapa de folium con índice de vegetación de diferencia normalizada

        Args:

        Returns:
            [Json]:
        """
        today = date.today()
        date_today = today.strftime('%Y-%m-%d')

        s1_collection = ee.ImageCollection('COPERNICUS/S1_GRD')\
            .filter(ee.Filter.listContains('transmitterReceiverPolarisation', 'VV'))\
            .filter(ee.Filter.eq('orbitProperties_pass', 'DESCENDING'))\
            .filter(ee.Filter.eq('instrumentMode', 'IW')).filterBounds(fc)

        s1_collection = s1_collection.filterDate('2022-01-01', date_today)

        def aoi_mean(img):

            mean = img.reduceRegion(
                reducer=ee.Reducer.mean(), geometry=fc, scale=10).get('VV')
            return img.set('date', img.date().format()).set('mean', mean)
        collection_reduced = s1_collection.map(aoi_mean)
        nested_list = collection_reduced.reduceColumns(
            ee.Reducer.toList(2), ['date', 'mean']).values().get(0)
        df = pd.DataFrame(nested_list.getInfo(), columns=['date', 'mean'])
        df['date'] = pd.to_datetime(df['date']).dt.strftime('%Y-%m-%d')
        df = df.groupby(['date']).mean()
        df = df.reset_index()
        df['mean'] = df['mean'].astype(float).round(2)
        dates_ts = list(df['date'])
        mean_ts = list(df['mean'])
        dict_ts = {'dates': dates_ts, 'mean_ts': mean_ts}
        return dict_ts

    def ts_sar_vh(fc):
        """Función que obtiene mapa de folium con índice de vegetación de diferencia normalizada

        Args:

        Returns:
            [Json]:
        """
        today = date.today()
        date_today = today.strftime('%Y-%m-%d')

        s1_collection = ee.ImageCollection('COPERNICUS/S1_GRD')\
            .filter(ee.Filter.listContains('transmitterReceiverPolarisation', 'VV'))\
            .filter(ee.Filter.eq('orbitProperties_pass', 'DESCENDING'))\
            .filter(ee.Filter.eq('instrumentMode', 'IW')).filterBounds(fc)

        s1_collection = s1_collection.filterDate('2022-01-01', date_today)

        def aoi_mean(img):

            mean = img.reduceRegion(
                reducer=ee.Reducer.mean(), geometry=fc, scale=10).get('VH')
            return img.set('date', img.date().format()).set('mean', mean)
        collection_reduced = s1_collection.map(aoi_mean)
        nested_list = collection_reduced.reduceColumns(
            ee.Reducer.toList(2), ['date', 'mean']).values().get(0)
        df = pd.DataFrame(nested_list.getInfo(), columns=['date', 'mean'])
        df['date'] = pd.to_datetime(df['date']).dt.strftime('%Y-%m-%d')
        df = df.groupby(['date']).mean()
        df = df.reset_index()
        df['mean'] = df['mean'].astype(float).round(2)
        dates_ts = list(df['date'])
        mean_ts = list(df['mean'])
        dict_ts = {'dates': dates_ts, 'mean_ts': mean_ts}
        return dict_ts
