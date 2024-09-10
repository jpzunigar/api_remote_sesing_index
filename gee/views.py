from django.shortcuts import render
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from gee.map_functions_2 import MapFunctions
from gee.time_series import TimeSeries
from gee.ExceptionsManager import WrongZipFile
import ee
from datetime import date
import os
import environ

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
env = environ.Env()


service_account = env("SERVICE_ACCOUNT")
credentials = ee.ServiceAccountCredentials(
    service_account, os.path.join(BASE_DIR, 'static', 'temp', env("SERVICE_ACCOUNT_KEY")))
ee.Initialize(credentials)


class CalculatedMapsAPI(APIView):
    def post(self, request):

        try:
            data = request.data
            date = data['date_data']
            producto = data['producto']
            if data['drew_geojson']:
                aoi, fc = MapFunctions.Make_AOI(
                    drew_geometry=data['drew_geojson'])
            else:
                raise Exception(
                    "no se ha dibujado el AOI, por favor dibuje el AOI")
            if producto == 'NDVI':
                result = MapFunctions.GetIndexNDVI(date, aoi, fc)
            elif producto == 'EVI':
                result = MapFunctions.GetIndexEVI(date, aoi, fc)
            elif producto == 'SAR-VH':
                result = MapFunctions.GetSarVH(date, aoi, fc)
            elif producto == 'SAR-VV':
                result = MapFunctions.GetSarVV(date, aoi, fc)
            elif producto == 'NDMI':
                result = MapFunctions.GetIndexNDMI(date, aoi, fc)
            elif producto == 'CIG':
                result = MapFunctions.GetIndexCIG(date, aoi, fc)
            else:
                raise Exception("no está en la lista de opciones")
            return Response(result, status=status.HTTP_200_OK)
        except Exception as e:
            return Response(str(e),
                            status=status.HTTP_500_INTERNAL_SERVER_ERROR)


class TimeSeriesView(APIView):
    def post(self, request):

        try:
            data = request.data
            producto = data['producto']
            if data['drew_geojson']:
                _, fc = MapFunctions.Make_AOI(
                    drew_geometry=data['drew_geojson'])
            else:
                raise Exception(
                    "no se ha dibujado el AOI, por favor dibuje el AOI")
            if producto == 'NDVI':
                result = TimeSeries.ts_ndvi(fc)
            elif producto == 'EVI':
                result = TimeSeries.ts_evi(fc)
            elif producto == 'SAR-VH':
                result = TimeSeries.ts_sar_vv(fc)
            elif producto == 'SAR-VV':
                result = TimeSeries.ts_sar_vh(fc)
            elif producto == 'NDMI':
                result = TimeSeries.ts_ndmi(fc)
            elif producto == 'CIG':
                result = TimeSeries.ts_cig(fc)
            else:
                raise Exception("no está en la lista de opciones")
            return Response(result, status=status.HTTP_200_OK)
        except Exception as e:
            return Response(str(e),
                            status=status.HTTP_500_INTERNAL_SERVER_ERROR)


class DatesWithImages(APIView):

    def post(self, request):
        """Vista para obtener las fechas a quitar y el id asociado a cada fecha de imagen disponible

        Args:
            request ([type]): peticion

        Returns:
            [type]: geojson, list
        """
        try:
            data = request.data
            if data['drew_geojson']:
                aoi, _ = MapFunctions.Make_AOI(
                    drew_geometry=data['drew_geojson'])
                if data['producto'] == 'NDVI' or data['producto'] == 'EVI' or data['producto'] == 'CIG' or data['producto'] == 'NDMI':
                    dates = MapFunctions.GetDateS2(aoi)
                else:
                    dates = MapFunctions.GetDateS1(aoi)

            else:
                hda_lote = data['hda_lote']
                producto = data['producto']
                aoi, _ = MapFunctions.Make_AOI(hda_lote)
                if producto == 'NDVI' or producto == 'EVI' or producto == 'CIG' or producto == 'NDMI':
                    dates = MapFunctions.GetDateS2(aoi)
                else:
                    dates = MapFunctions.GetDateS1(aoi)
            return Response(dates, status=status.HTTP_200_OK)
        except Exception as e:
            return Response(str(e),
                            status=status.HTTP_500_INTERNAL_SERVER_ERROR)