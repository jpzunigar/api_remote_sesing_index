import ee
import numpy as np
from datetime import datetime
from affine import Affine
from rasterio.crs import CRS

class GeeUtils:

    def correct_coords(xMin, yMax, XminAOI, YmaxAOI):
        """función para corregir las coordenadas origen de la imagen

        Args:
            xMin (Float): Coordenada X del origen de la imagen
            yMax (Float): Coordenada Y del origen de la imagen
        Returns:
            [Float, Float]: Coordenada X corregida, Coordenada Y corregida
        """
        if xMin > XminAOI and yMax < YmaxAOI:
            xMin = xMin - 10
            yMax = yMax + 10
        elif xMin > XminAOI and yMax > YmaxAOI:
            xMin = xMin - 10
        elif xMin < XminAOI and yMax < YmaxAOI:
            yMax = yMax + 10
        else:
            xMin = xMin
            yMax = yMax
        return xMin, yMax

    def get_data_eeImage(eeIndex, AOI, XminAOI, YmaxAOI):
        """función para extraer la informacion del raster de GEE

        Args:
            eeIndex (ee.Image): Imagen de GEE del producto
            AOI (ee.geometry): Poligono que delimita la extensión de la suerte
            XminAOI (Float): Coordenada X min del shape
            YmaxAOI (Float): Coordenada Y min del shape
        Returns:
            [Float, Float]: Coordenada X corregida, Coordenada Y corregida
        """
        projection_ori = eeIndex.projection()
        proj32618 = ee.Projection('EPSG:32618')
        Image_coords = eeIndex.pixelCoordinates(proj32618).reproject(projection_ori)
        prueba = Image_coords.reduceRegion(ee.Reducer.toList(), AOI, scale = 10)
        IndexID = eeIndex.bandNames().getInfo()[0]
        CoordsY = np.array(prueba.get('y').getInfo())
        CoordsX = np.array(prueba.get('x').getInfo())
        xMin, yMax = [CoordsX.min() - 5, CoordsY.max() + 5]
        xMin, yMax = GeeUtils.correct_coords(xMin, yMax, XminAOI, YmaxAOI)
        band_arrs = eeIndex.sampleRectangle(region = AOI)
        name_id = list(band_arrs.getInfo()['properties'].keys())[0]
        band_arr_index = band_arrs.get(name_id)
        np_arr_index = np.array(band_arr_index.getInfo())
        geotransform = (xMin, 10, 0, yMax, 0, -10)
        rows, columns, data_type = np_arr_index.shape[0], np_arr_index.shape[1], np_arr_index.dtype
        # Getting the current date and time
        fwd = Affine.from_gdal(*geotransform)
        dt = datetime.now()
        # getting the timestamp
        ts = datetime.timestamp(dt)
        crs = CRS.from_epsg(32618)
        data_image = {'index' : np_arr_index, 'height': rows, 'width': columns, 'dtype': str(data_type), 'crs' : crs, 'transform': fwd, 'NoData':-9999, 'Bandas': 1, 'Name_TimeStap': IndexID + '_' + str(int(ts)) + '.tif'}
        return data_image
    
    def maskS2clouds(image):
        """Función para enmascarar las nubes utilizando la banda QA de Sentinel-2

        Args:
            image (ee.image, ee.ImageCollection): Imagen de Sentinel 2

        Returns:
            [ee.image, ee.ImageCollection]: Imagen enmascarada de nubes
        """
        qa = image.select('QA60')
        # Los bits 10 y 11 son nubes y cirros, respectivamente.
        cloudBitMask = 1 << 10
        cirrusBitMask = 1 << 11
        # Ambas banderas deben ponerse a cero, lo que indica que las condiciones son claras.
        mask = qa.bitwiseAnd(cloudBitMask).eq(0)
        mask = mask.bitwiseAnd(cirrusBitMask).eq(0)
        return image.updateMask(mask).copyProperties(image, ['system:time_start'])
    
    def mask_s2clouds_v2(image):
        qa = image.select('QA60')
        # Bits 10 and 11 are clouds and cirrus, respectively.
        cloud_bit_mask = 1 << 10
        cirrus_bit_mask = 1 << 11
        # Both flags should be set to zero, indicating clear conditions.
        mask = qa.bitwiseAnd(cloud_bit_mask).eq(0) \
            .And(qa.bitwiseAnd(cirrus_bit_mask).eq(0))
        return image.updateMask(mask)


    def IndexNDVI(img):
        """Función para calcular Índice de vegetación de diferencia normalizada en imaganes Sentinel 2

        Args:
            img (ee.image, ee.ImageCollection): Imagen o imagenes a las que se le calcula el índice

        Returns:
            [ee.image, ee.ImageCollection]: Adiciona la banda del producto a la imagen
        """     
        ndvi = img.normalizedDifference(['B8', 'B4']).rename("NDVI")
        return ndvi
    
    def indexNDVI_ts(img):
        """Función para calcular Índice de vegetación de diferencia normalizada en imaganes Sentinel 2

        Args:
            img (ee.image, ee.ImageCollection): Imagen o imagenes a las que se le calcula el índice

        Returns:
            [ee.image, ee.ImageCollection]: Adiciona la banda del producto a la imagen
        """    
        NDVI = img.normalizedDifference(['B8','B4']).rename('NDVI')
        return img.addBands(NDVI)

    def IndexEVI_ts(Collection):
        """Función para calcular Índice de vegetación mejorado

        Args:
            img (ee.image, ee.ImageCollection): Imagen o imagenes a las que se le calcula el índice

        Returns:
            [ee.image, ee.ImageCollection]: Adiciona la banda del producto a la imagen
        """
        evi = Collection.expression('2.5 * ((NIR - RED) / (((NIR + (6 * RED)) - (7.5 * BLUE)) + 1))', 
                                    {'NIR' : Collection.select('B8').divide(10000), 
                                     'RED' : Collection.select('B4').divide(10000), 
                                     'BLUE' : Collection.select('B2').divide(10000)}).rename(['EVI'])
        return Collection.addBands(evi)

    def IndexEVI(Collection):
        """Función para calcular Índice de vegetación mejorado

        Args:
            img (ee.image, ee.ImageCollection): Imagen o imagenes a las que se le calcula el índice

        Returns:
            [ee.image, ee.ImageCollection]: Adiciona la banda del producto a la imagen
        """
        Collection = Collection.divide(10000)
        evi = Collection.expression('2.5 * ((NIR - RED) / (((NIR + (6 * RED)) - (7.5 * BLUE)) + 1))', {'NIR' : Collection.select('B8'), 'RED' : Collection.select('B4'), 'BLUE' : Collection.select('B2')}).rename(['EVI'])
        return evi
    
    def indexNDMI(collection):
        NDMI = collection.normalizedDifference(['B8','B11']).rename('NDMI')
        return collection.addBands(NDMI)
    
    def indexCIG(collection):
        CIG = collection.expression('(NIR/GREEN) - 1', {'NIR' : collection.select('B8'), 'GREEN' : collection.select('B3')}).rename(['CIG'])
        return collection.addBands(CIG)