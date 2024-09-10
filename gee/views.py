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
import logging

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
env = environ.Env()


service_account = env("SERVICE_ACCOUNT")
credentials = ee.ServiceAccountCredentials(
    service_account, os.path.join(BASE_DIR, 'static', 'temp', env("SERVICE_ACCOUNT_KEY")))
ee.Initialize(credentials)


logger = logging.getLogger(__name__)

class CalculatedMapsAPI(APIView):
    def post(self, request):
        try:
            data = request.data
            date_data = data.get('date_data')
            producto = data.get('producto')
            drew_geojson = data.get('drew_geojson')

            if not date_data:
                return Response({'error': 'Date data is required.'}, status=status.HTTP_400_BAD_REQUEST)
            if not producto:
                return Response({'error': 'Producto is required.'}, status=status.HTTP_400_BAD_REQUEST)
            if not drew_geojson:
                return Response({'error': 'No AOI was drawn. Please provide a valid AOI.'}, status=status.HTTP_400_BAD_REQUEST)
            
            # Process the AOI
            try:
                aoi, fc = MapFunctions.Make_AOI(drew_geometry=drew_geojson)
            except ValueError as e:
                logger.error(f"Invalid AOI geometry: {e}")
                return Response({'error': 'Invalid AOI geometry.'}, status=status.HTTP_400_BAD_REQUEST)

            # Determine the product and calculate the result
            try:
                if producto == 'NDVI':
                    result = MapFunctions.GetIndexNDVI(date_data, aoi, fc)
                elif producto == 'EVI':
                    result = MapFunctions.GetIndexEVI(date_data, aoi, fc)
                elif producto == 'SAR-VH':
                    result = MapFunctions.GetSarVH(date_data, aoi, fc)
                elif producto == 'SAR-VV':
                    result = MapFunctions.GetSarVV(date_data, aoi, fc)
                elif producto == 'NDMI':
                    result = MapFunctions.GetIndexNDMI(date_data, aoi, fc)
                elif producto == 'CIG':
                    result = MapFunctions.GetIndexCIG(date_data, aoi, fc)
                else:
                    return Response({'error': 'Invalid product option.'}, status=status.HTTP_400_BAD_REQUEST)
            except Exception as e:
                logger.error(f"Error in Map Function calculation: {e}")
                return Response({'error': 'Failed to process the request.'}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

            return Response(result, status=status.HTTP_200_OK)
        
        except KeyError as e:
            logger.error(f"Missing required data: {e}")
            return Response({'error': f'Missing required field: {str(e)}'}, status=status.HTTP_400_BAD_REQUEST)
        except Exception as e:
            logger.error(f"Unexpected error: {e}")
            return Response({'error': 'An unexpected error occurred.'}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


class TimeSeriesView(APIView):
    def post(self, request):
        try:
            data = request.data
            producto = data.get('producto')
            drew_geojson = data.get('drew_geojson')

            if not producto:
                return Response({'error': 'Producto is required.'}, status=status.HTTP_400_BAD_REQUEST)
            if not drew_geojson:
                return Response({'error': 'No AOI was drawn. Please provide a valid AOI.'}, status=status.HTTP_400_BAD_REQUEST)

            # Process the AOI
            try:
                _, fc = MapFunctions.Make_AOI(drew_geometry=drew_geojson)
            except ValueError as e:
                logger.error(f"Invalid AOI geometry: {e}")
                return Response({'error': 'Invalid AOI geometry.'}, status=status.HTTP_400_BAD_REQUEST)

            # Calculate the time series based on the product
            try:
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
                    return Response({'error': 'Invalid product option.'}, status=status.HTTP_400_BAD_REQUEST)
            except Exception as e:
                logger.error(f"Error in time series calculation: {e}")
                return Response({'error': 'Failed to process time series data.'}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

            return Response(result, status=status.HTTP_200_OK)
        
        except KeyError as e:
            logger.error(f"Missing required data: {e}")
            return Response({'error': f'Missing required field: {str(e)}'}, status=status.HTTP_400_BAD_REQUEST)
        except Exception as e:
            logger.error(f"Unexpected error: {e}")
            return Response({'error': 'An unexpected error occurred.'}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


class DatesWithImages(APIView):
    def post(self, request):
        try:
            data = request.data
            producto = data.get('producto')
            drew_geojson = data.get('drew_geojson')

            if not producto:
                return Response({'error': 'Producto is required.'}, status=status.HTTP_400_BAD_REQUEST)
            if not drew_geojson:
                return Response({'error': 'No AOI was drawn. Please provide a valid AOI.'}, status=status.HTTP_400_BAD_REQUEST)

            # Process the AOI
            try:
                aoi, _ = MapFunctions.Make_AOI(drew_geometry=drew_geojson)
            except ValueError as e:
                logger.error(f"Invalid AOI geometry: {e}")
                return Response({'error': 'Invalid AOI geometry.'}, status=status.HTTP_400_BAD_REQUEST)

            # Fetch dates based on the product
            try:
                if producto in ['NDVI', 'EVI', 'CIG', 'NDMI']:
                    dates = MapFunctions.GetDateS2(aoi)
                else:
                    dates = MapFunctions.GetDateS1(aoi)
            except Exception as e:
                logger.error(f"Error fetching dates: {e}")
                return Response({'error': 'Failed to fetch available dates.'}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

            return Response(dates, status=status.HTTP_200_OK)

        except KeyError as e:
            logger.error(f"Missing required data: {e}")
            return Response({'error': f'Missing required field: {str(e)}'}, status=status.HTTP_400_BAD_REQUEST)
        except Exception as e:
            logger.error(f"Unexpected error: {e}")
            return Response({'error': 'An unexpected error occurred.'}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
