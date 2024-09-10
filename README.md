# Django GeoSpatial API Project

This project provides several REST API endpoints to calculate geospatial indices and retrieve time-series data using Google Earth Engine (GEE). The APIs handle spatial data such as AOIs (Areas of Interest) and various products like NDVI, EVI, SAR-VH, etc. The project is built using Django and Django Rest Framework (DRF).

## Table of Contents

- [Project Setup](#project-setup)
- [Environment Variables](#environment-variables)
- [Available Endpoints](#available-endpoints)
  - [CalculatedMapsAPI](#calculatedmapsapi)
  - [TimeSeriesView](#timeseriesview)
  - [DatesWithImages](#dateswithimages)
- [Error Handling](#error-handling)
- [Logging](#logging)
- [Contributing](#contributing)

---

## Project Setup

To get started, follow the steps below:

1. **Clone the repository**:
    ```bash
   git clone https://github.com/yourusername/django-geospatial-api.git
   cd django-geospatial-api
2. **Install dependencies**:This project uses pipenv for managing dependencies:
    ```bash
    pip install -r requirements.txt
3. **Set up the environment**:
    Create a .env file in the root directory and define the required environment variables (see example.env).
4.  **Run the development server**: Start the Django server:
     ```bash
    python manage.py runserver

## Available Endpoints
1. POST /api/calculate-maps/

This endpoint calculates geospatial indices (NDVI, EVI, SAR-VH, etc.) for a specific date and Area of Interest (AOI).
Request Body:
    ```json
    {
        "date_data": "YYYY-MM-DD",
        "producto": "NDVI",
        "drew_geojson": "geojson_representation_of_AOI"
    }
    ```

**Response**:
    **200 OK**: The calculated geospatial product.
    **400 Bad Request**: Missing or invalid input data.
    **500 Internal Server Error**: Server error during processing.

2. POST /api/time-series/
This endpoint returns a time series of a given geospatial product for an AOI.
Request Body:
    ```json
        json

        {
            "producto": "NDVI",
            "drew_geojson": "geojson_representation_of_AOI"
        }
    ```

**Response**:
    **200 OK**: Time series data.
    **400 Bad Request**: Missing or invalid input data.
    **500 Internal Server Error**: Error fetching time series data.

3. POST /api/dates_with_images/

This endpoint returns available dates with imagery for the requested product and AOI.
Request Body:

    ```json
        json

        {
        "producto": "NDVI",
        "drew_geojson": "geojson_representation_of_AOI"
        }
    ```

**Response**:
    **200 OK**: List of available dates.
    **400 Bad Request**: Missing or invalid input data.
    **500 Internal Server Error**: Error fetching available dates.

## Error Handling

The API handles various errors, such as:

    -400 Bad Request: If required fields are missing or invalid.
    -500 Internal Server Error: For unexpected errors or failures in third-party services (e.g., Google Earth Engine).

Common errors include:

    -Missing date_data, producto, or drew_geojson.
    -Invalid AOI geometry.

## Logging
This project uses Python’s logging module to log errors. Logs are stored in the default Django loggers. You can configure the logging settings in settings.py.

License

This project is licensed under the MIT License.

### Key sections:

1. **Project Setup**: Instructions to clone, install dependencies, and run the project.
2. **Environment Variables**: Explanation of required environment variables (for accessing Google Earth Engine).
3. **Available Endpoints**: Detailed API documentation, including request body and expected responses for each view.
4. **Error Handling**: Information on common errors and their handling.
5. **Logging**: Overview of how logging is managed in the project.
6. **Contributing**: Basic guidelines on how to contribute to the project.

This structure can be expanded or customized depending on your specific project needs.


