import ee
from gee.gee_utils import GeeUtils
from geemap import geojson_to_ee
from ee import ImageCollection
from ee import Filter
from django.contrib.gis.geos import GEOSGeometry
from django.contrib.gis.geos import GeometryCollection
from ee import Geometry
from datetime import date
from datetime import datetime, timedelta
from gee.functions import GeneralFunctions
import json
import io
import jenkspy
import zipfile
import numpy as np
from django.conf import settings
from gee.ExceptionsManager import WrongZipFile
import psycopg2
import os
import geopandas as gpd
import rasterio
from rasterio.warp import calculate_default_transform, reproject, Resampling
from PIL import Image
from shapely.geometry import box


# Build paths inside the project like this: BASE_DIR / 'subdir'.
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


class MapFunctions:
    def GetDateS2(AOI):
        today = date.today()
        date_today = today.strftime('%Y-%m-%d')

        s2_collection = ImageCollection('COPERNICUS/S2_SR_HARMONIZED').filterDate('2020-01-01', date_today)\
            .filterBounds(AOI).filter(Filter.lte('CLOUDY_PIXEL_PERCENTAGE', 60))
        # s2_collection = ImageCollection('COPERNICUS/S2_SR_HARMONIZED').filterDate('2020-01-01', date_today)\
        #     .filterBounds(AOI)

        dates = s2_collection.aggregate_array('system:time_start')
        image_ids = s2_collection.aggregate_array('system:id')

        dates_list = dates.getInfo()
        dates_list = [datetime.utcfromtimestamp(
            date / 1000).strftime('%Y-%m-%d') for date in dates_list]
        image_ids_list = image_ids.getInfo()
        image_info_dict = {}

        for date_img, image_id in zip(dates_list, image_ids_list):
            image_info_dict[date_img] = image_id

        dates_list_complete = GeneralFunctions.get_list_dates()
        dates_list_no_data = [
            fecha for fecha in dates_list_complete if fecha not in dates_list]

        return {'dates_data': image_info_dict, 'dates_no_data': dates_list_no_data}

    def GetDateS1(AOI):
        today = date.today()
        date_today = today.strftime('%Y-%m-%d')

        s1_collection = ee.ImageCollection('COPERNICUS/S1_GRD').filterDate('2020-01-01', date_today)\
            .filter(ee.Filter.listContains('transmitterReceiverPolarisation', 'VV'))\
            .filter(ee.Filter.eq('orbitProperties_pass', 'DESCENDING'))\
            .filter(ee.Filter.eq('instrumentMode', 'IW')).filterBounds(AOI)

        dates = s1_collection.aggregate_array('system:time_start')
        image_ids = s1_collection.aggregate_array('system:id')

        dates_list = dates.getInfo()
        dates_list = [datetime.utcfromtimestamp(
            date / 1000).strftime('%Y-%m-%d') for date in dates_list]
        image_ids_list = image_ids.getInfo()
        image_info_dict = {}

        for date_img, image_id in zip(dates_list, image_ids_list):
            image_info_dict[date_img] = image_id

        dates_list_complete = GeneralFunctions.get_list_dates()
        dates_list_no_data = [
            fecha for fecha in dates_list_complete if fecha not in dates_list]

        return {'dates_data': image_info_dict, 'dates_no_data': dates_list_no_data}

    def GetIndexNDVI(date, AOI, fc):
        """Función que obtiene mapa de folium con índice de vegetación de diferencia normalizada

        Args:

        Returns:
            [Json]:
        """
        fecha_objeto = datetime.strptime(date, '%Y-%m-%d')
        second_date = fecha_objeto + timedelta(days=1)
        second_date = second_date.strftime('%Y-%m-%d')
        s2_collection = ImageCollection(
            'COPERNICUS/S2_SR_HARMONIZED').filterBounds(AOI)
        s2_collection = s2_collection.filterDate(date, second_date)
        img_S2 = s2_collection.mean()
        img_S2 = img_S2.clip(AOI)
        # img_S2 = GeeUtils.mask_s2clouds_v2(img_S2)
        s2_Index = GeeUtils.IndexNDVI(img_S2)
        bounds = s2_Index.geometry().bounds()

        product_stats = s2_Index.select('NDVI').reduceRegion(
            reducer=ee.Reducer.percentile([25, 50, 75]),
            geometry=fc,
            scale=10
        )
        low = round(product_stats.getInfo()['NDVI_p25'], 2)
        med = round(product_stats.getInfo()['NDVI_p50'], 2)
        high = round(product_stats.getInfo()['NDVI_p75'], 2)
        classified = s2_Index.select('NDVI').expression(
            "(b('NDVI') < low) ? 0" +  # Low vegetation
            ": (b('NDVI') < med) ? 1" +  # Medium vegetation
            ": (b('NDVI') < high) ? 2" +  # High vegetation
            ": 3",  # Non-vegetated
            {'low': low, 'med': med, 'high': high}
        )
        palette = ['2d0407', '67ea20', '12fc12', '064106']
        legendList = [{'label': f" < {round(low, 2)}", 'color': "#2d0407"},
                      {'label': f"{round(low, 2)} - {round(med, 2)}",
                       'color': "#67ea20"},
                      {'label': f"{round(med, 2)} - {round(high, 2)}",
                       'color': "#12fc12"},
                      {'label': f" > {round(high, 2)}", 'color': "#064106"}
                      ]
        # Extract minimum and maximum coordinates
        min_coords = bounds.getInfo()['coordinates'][0][0]
        max_coords = bounds.getInfo()['coordinates'][0][2]
        min_longitude, min_latitude = min_coords
        max_longitude, max_latitude = max_coords

        url_index = classified.clip(fc).getThumbURL({
            'min': 0,
            'max': 3,
            'palette': palette,
            'region': AOI,
            'dimensions': 1000,
            'format': 'png'
        })
        return {'path_image': url_index, 'min_lon': min_longitude, 'max_lon': max_longitude,
                'min_lat': min_latitude, 'max_lat': max_latitude, 'legendList': legendList}

    def GetIndexEVI(date, AOI, fc):
        """Función que obtiene mapa de folium con índice de vegetación mejorado
        Args:

        Returns:
            [Json]:
        """
        fecha_objeto = datetime.strptime(date, '%Y-%m-%d')
        second_date = fecha_objeto + timedelta(days=1)
        second_date = second_date.strftime('%Y-%m-%d')
        s2_collection = ImageCollection(
            'COPERNICUS/S2_SR_HARMONIZED').filterBounds(AOI)
        s2_collection = s2_collection.filterDate(date, second_date)
        img_S2 = s2_collection.mean()
        s2_Index = GeeUtils.IndexEVI(img_S2).clip(AOI)
        bounds = s2_Index.geometry()
        s2_Index = s2_Index.gt(1).multiply(1).add(
            s2_Index.lt(1).multiply(s2_Index))

        product_stats = s2_Index.select('EVI').reduceRegion(
            reducer=ee.Reducer.percentile([25, 50, 75, 100]),
            geometry=fc,
            scale=10
        )

        low = round(product_stats.getInfo()['EVI_p25'], 2)
        med = round(product_stats.getInfo()['EVI_p50'], 2)
        high = round(product_stats.getInfo()['EVI_p75'], 2)
        classified = s2_Index.select('EVI').expression(
            "(b('EVI') < low) ? 0" +  # Low vegetation
            ": (b('EVI') < med) ? 1" +  # Medium vegetation
            ": (b('EVI') < high) ? 2" +  # High vegetation
            ": 3",  # Non-vegetated
            {'low': low, 'med': med, 'high': high}
        )
        palette = ['2d0407', '67ea20', '12fc12', '064106']
        legendList = [{'label': f" < {round(low, 2)}", 'color': "#2d0407"},
                      {'label': f"{round(low, 2)} - {round(med, 2)}",
                       'color': "#67ea20"},
                      {'label': f"{round(med, 2)} - {round(high, 2)}",
                       'color': "#12fc12"},
                      {'label': f" > {round(high, 2)}", 'color': "#064106"}
                      ]
        # Extract minimum and maximum coordinates
        min_coords = bounds.getInfo()['coordinates'][0][0]
        max_coords = bounds.getInfo()['coordinates'][0][2]
        min_longitude, min_latitude = min_coords
        max_longitude, max_latitude = max_coords
        url_index = classified.clip(fc).getThumbURL({
            'min': 0,
            'max': 3,
            'palette': palette,
            'region': AOI,
            'dimensions': 1000,
            'format': 'png'
        })
        return {'path_image': url_index, 'min_lon': min_longitude, 'max_lon': max_longitude,
                'min_lat': min_latitude, 'max_lat': max_latitude, 'legendList': legendList}

    def GetIndexNDMI(date, AOI, fc):
        """Función que obtiene mapa de folium con índice de vegetación mejorado
        Args:

        Returns:
            [Json]:
        """
        fecha_objeto = datetime.strptime(date, '%Y-%m-%d')
        second_date = fecha_objeto + timedelta(days=1)
        second_date = second_date.strftime('%Y-%m-%d')
        s2_collection = ImageCollection(
            'COPERNICUS/S2_SR_HARMONIZED').filterBounds(AOI)
        s2_collection = s2_collection.filterDate(date, second_date)
        img_S2 = s2_collection.mean()
        s2_Index = GeeUtils.indexNDMI(img_S2).clip(AOI)
        bounds = s2_Index.geometry()
        product_stats = s2_Index.select('NDMI').reduceRegion(
            reducer=ee.Reducer.percentile([25, 50, 75, 100]),
            geometry=fc,
            scale=10
        )

        low = round(product_stats.getInfo()['NDMI_p25'], 2)
        med = round(product_stats.getInfo()['NDMI_p50'], 2)
        high = round(product_stats.getInfo()['NDMI_p75'], 2)
        classified = s2_Index.select('NDMI').expression(
            "(b('NDMI') < low) ? 0" +  # Low vegetation
            ": (b('NDMI') < med) ? 1" +  # Medium vegetation
            ": (b('NDMI') < high) ? 2" +  # High vegetation
            ": 3",  # Non-vegetated
            {'low': low, 'med': med, 'high': high}
        )
        palette = ['ff1f0a', '0eded7', '2b6ea6', '08306b']
        legendList = [{'label': f" < {round(low, 2)}", 'color': "#ff1f0a"},
                      {'label': f"{round(low, 2)} - {round(med, 2)}",
                       'color': "#0eded7"},
                      {'label': f"{round(med, 2)} - {round(high, 2)}",
                       'color': "#2b6ea6"},
                      {'label': f" > {round(high, 2)}", 'color': "#08306b"}
                      ]

        # Extract minimum and maximum coordinates
        min_coords = bounds.getInfo()['coordinates'][0][0]
        max_coords = bounds.getInfo()['coordinates'][0][2]
        min_longitude, min_latitude = min_coords
        max_longitude, max_latitude = max_coords
        url_index = classified.clip(fc).getThumbURL({
            'min': 0,
            'max': 3,
            'palette': palette,
            'region': AOI,
            'dimensions': 1000,
            'format': 'png'
        })
        return {'path_image': url_index, 'min_lon': min_longitude, 'max_lon': max_longitude,
                'min_lat': min_latitude, 'max_lat': max_latitude, 'legendList': legendList}

    def GetIndexCIG(date, AOI, fc):
        """Función que obtiene mapa de folium con índice de vegetación mejorado
        Args:

        Returns:
            [Json]:
        """
        fecha_objeto = datetime.strptime(date, '%Y-%m-%d')
        second_date = fecha_objeto + timedelta(days=1)
        second_date = second_date.strftime('%Y-%m-%d')
        s2_collection = ImageCollection(
            'COPERNICUS/S2_SR_HARMONIZED').filterBounds(AOI)
        s2_collection = s2_collection.filterDate(date, second_date)
        img_S2 = s2_collection.mean()
        s2_Index = GeeUtils.indexCIG(img_S2).clip(AOI)
        bounds = s2_Index.geometry()
        product_stats = s2_Index.select('CIG').reduceRegion(
            reducer=ee.Reducer.percentile([25, 50, 75, 100]),
            geometry=fc,
            scale=10
        )

        low = round(product_stats.getInfo()['CIG_p25'], 2)
        med = round(product_stats.getInfo()['CIG_p50'], 2)
        high = round(product_stats.getInfo()['CIG_p75'], 2)
        classified = s2_Index.select('CIG').expression(
            "(b('CIG') < low) ? 0" +  # Low vegetation
            ": (b('CIG') < med) ? 1" +  # Medium vegetation
            ": (b('CIG') < high) ? 2" +  # High vegetation
            ": 3",  # Non-vegetated
            {'low': low, 'med': med, 'high': high}
        )
        palette = ['2d0407', '67ea20', '12fc12', '064106']
        legendList = [{'label': f" < {round(low, 2)}", 'color': "#2d0407"},
                      {'label': f"{round(low, 2)} - {round(med, 2)}",
                       'color': "#67ea20"},
                      {'label': f"{round(med, 2)} - {round(high, 2)}",
                       'color': "#12fc12"},
                      {'label': f" > {round(high, 2)}", 'color': "#064106"}
                      ]
        # Extract minimum and maximum coordinates
        min_coords = bounds.getInfo()['coordinates'][0][0]
        max_coords = bounds.getInfo()['coordinates'][0][2]
        min_longitude, min_latitude = min_coords
        max_longitude, max_latitude = max_coords
        url_index = classified.clip(fc).getThumbURL({
            'min': 0,
            'max': 3,
            'palette': palette,
            'region': AOI,
            'dimensions': 1000,
            'format': 'png'
        })
        return {'path_image': url_index, 'min_lon': min_longitude, 'max_lon': max_longitude,
                'min_lat': min_latitude, 'max_lat': max_latitude, 'legendList': legendList}

    def GetSarVH(date, AOI, fc):
        """Función que obtiene mapa de folium con índice de vegetación mejorado
        Args:

        Returns:
            [Json]:
        """

        fecha_objeto = datetime.strptime(date, '%Y-%m-%d')
        second_date = fecha_objeto + timedelta(days=1)
        second_date = second_date.strftime('%Y-%m-%d')
        s1_collection = ee.ImageCollection('COPERNICUS/S1_GRD')\
            .filter(ee.Filter.listContains('transmitterReceiverPolarisation', 'VV'))\
            .filter(ee.Filter.eq('orbitProperties_pass', 'DESCENDING'))\
            .filter(ee.Filter.eq('instrumentMode', 'IW')).filterBounds(AOI)

        s1_collection = s1_collection.filterDate(date, second_date)
        S1_polarization = s1_collection.mosaic()
        S1_polarization = S1_polarization.select('VH').clip(AOI)
        bounds = S1_polarization.geometry()
        product_stats = S1_polarization.reduceRegion(
            reducer=ee.Reducer.percentile([25, 50, 75, 100]),
            geometry=fc,
            scale=10
        )
        low = round(product_stats.getInfo()['VH_p25'], 2)
        med = round(product_stats.getInfo()['VH_p50'], 2)
        high = round(product_stats.getInfo()['VH_p75'], 2)
        classified = S1_polarization.select('VH').expression(
            "(b('VH') < low) ? 0" +  # Low vegetation
            ": (b('VH') < med) ? 1" +  # Medium vegetation
            ": (b('VH') < high) ? 2" +  # High vegetation
            ": 3",  # Non-vegetated
            {'low': low, 'med': med, 'high': high}
        )
        palette = ['ff1f0a', '0eded7', '2b6ea6', '08306b']
        legendList = [{'label': f" < {round(low, 2)}", 'color': "#ff1f0a"},
                      {'label': f"{round(low, 2)} - {round(med, 2)}",
                       'color': "#0eded7"},
                      {'label': f"{round(med, 2)} - {round(high, 2)}",
                       'color': "#2b6ea6"},
                      {'label': f" > {round(high, 2)}", 'color': "#08306b"}
                      ]
        # Extract minimum and maximum coordinates
        min_coords = bounds.getInfo()['coordinates'][0][0]
        max_coords = bounds.getInfo()['coordinates'][0][2]
        min_longitude, min_latitude = min_coords
        max_longitude, max_latitude = max_coords
        url_index = classified.clip(fc).getThumbURL({
            'min': 0,
            'max': 3,
            'palette': palette,
            'region': AOI,
            'dimensions': 1000,
            'format': 'png'
        })
        return {'path_image': url_index, 'min_lon': min_longitude, 'max_lon': max_longitude,
                'min_lat': min_latitude, 'max_lat': max_latitude, 'legendList': legendList}

    def GetSarVV(date, AOI, fc):
        """Función que obtiene mapa de folium con índice de vegetación mejorado
        Args:

        Returns:
            [Json]:
        """
        fecha_objeto = datetime.strptime(date, '%Y-%m-%d')
        second_date = fecha_objeto + timedelta(days=1)
        second_date = second_date.strftime('%Y-%m-%d')
        s1_collection = ee.ImageCollection('COPERNICUS/S1_GRD')\
            .filter(ee.Filter.listContains('transmitterReceiverPolarisation', 'VV'))\
            .filter(ee.Filter.eq('orbitProperties_pass', 'DESCENDING'))\
            .filter(ee.Filter.eq('instrumentMode', 'IW')).filterBounds(AOI)

        s1_collection = s1_collection.filterDate(date, second_date)
        S1_polarization = s1_collection.mosaic()
        S1_polarization = S1_polarization.select('VV').clip(AOI)
        bounds = S1_polarization.geometry()
        product_stats = S1_polarization.reduceRegion(
            reducer=ee.Reducer.percentile([25, 50, 75, 100]),
            geometry=fc,
            scale=10
        )

        low = round(product_stats.getInfo()['VV_p25'], 2)
        med = round(product_stats.getInfo()['VV_p50'], 2)
        high = round(product_stats.getInfo()['VV_p75'], 2)
        classified = S1_polarization.select('VV').expression(
            "(b('VV') < low) ? 0" +  # Low vegetation
            ": (b('VV') < med) ? 1" +  # Medium vegetation
            ": (b('VV') < high) ? 2" +  # High vegetation
            ": 3",  # Non-vegetated
            {'low': low, 'med': med, 'high': high}
        )
        palette = ['ff1f0a', '0eded7', '2b6ea6', '08306b']
        legendList = [{'label': f" < {round(low, 2)}", 'color': "#ff1f0a"},
                      {'label': f"{round(low, 2)} - {round(med, 2)}",
                       'color': "#0eded7"},
                      {'label': f"{round(med, 2)} - {round(high, 2)}",
                       'color': "#2b6ea6"},
                      {'label': f" > {round(high, 2)}", 'color': "#08306b"}
                      ]
        # Extract minimum and maximum coordinates
        min_coords = bounds.getInfo()['coordinates'][0][0]
        max_coords = bounds.getInfo()['coordinates'][0][2]
        min_longitude, min_latitude = min_coords
        max_longitude, max_latitude = max_coords
        url_index = classified.clip(fc).getThumbURL({
            'min': 0,
            'max': 3,
            'palette': palette,
            'region': AOI,
            'dimensions': 1000,
            'format': 'png'
        })
        return {'path_image': url_index, 'min_lon': min_longitude, 'max_lon': max_longitude,
                'min_lat': min_latitude, 'max_lat': max_latitude, 'legendList': legendList}

    def Make_AOI(hda_lote=None, drew_geometry=None):
        """función para construir geometrias de las haciendas y sus respectivas suertes

        Args:
            hacienda (string): codigo unico de la hacienda por su respectivo ingenio
            suerte (string): identificador de la suerte

        Returns:
            [ee.Geometry.Polygon]: Geometria de GEE de la extensión de la suerte
            [Float]: Coordenada X minima de la extensión de la suerte
            [Float]: Coordenada Y maxima de la extensión de la suerte
        """
        if drew_geometry:
            # Convert the geometry dict back to a GeoJSON string if necessary
            drew_geometry = json.dumps(drew_geometry)
            drew_geometry = json.loads(drew_geometry)

            # Convert the GeoJSON to an Earth Engine FeatureCollection
            feature_collection = geojson_to_ee(drew_geometry)

            # Get the bounding box (extent) in EPSG:4326 (assumes the geometry is in WGS84)
            coords_extent_4326 = feature_collection.bounds().getInfo(
            )['coordinates'][0]  # Extracting the bounding box

            # The coordinates are returned as a list of [xmin, ymin], [xmax, ymax], etc.
            xmin, ymin = coords_extent_4326[0]
            xmax, ymax = coords_extent_4326[2]

            # Create coordinates for the area of interest (AOI)
            coordenadas_AOI = [[xmin, ymin], [
                xmin, ymax], [xmax, ymax], [xmax, ymin]]

            # Create a polygon from the bounding box coordinates
            aoi = Geometry.Polygon(coordenadas_AOI)

            return aoi, feature_collection
        else:
            raise Exception("no se ha dibujado el AOI, por favor dibuje el AOI")
        


def reproject_tif_to_epsg4326(input_tif, output_tif):
    try:

        dst_crs = 'EPSG:4326'

        with rasterio.open(input_tif) as src:
            transform, width, height = calculate_default_transform(
                src.crs, dst_crs, src.width, src.height, *src.bounds)

            kwargs = src.meta.copy()
            kwargs.update({
                'crs': dst_crs,
                'transform': transform,
                'width': width,
                'height': height
            })

            with rasterio.open(output_tif, 'w', **kwargs) as dst:
                for i in range(1, src.count + 1):
                    reproject(
                        source=rasterio.band(src, i),
                        destination=rasterio.band(dst, i),
                        src_transform=src.transform,
                        src_crs=src.crs,
                        dst_transform=transform,
                        dst_crs=dst_crs,
                        resampling=Resampling.nearest)

    except:
        raise ValueError(
            'No se reprojecta el raster correctamente')


