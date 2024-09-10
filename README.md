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
1. POST /api/calculate_maps/

This endpoint calculates geospatial indices (NDVI, EVI, SAR-VH, etc.) for a specific date and Area of Interest (AOI).
Request Body:
    ```json
    {
        "date_data": "YYYY-MM-DD",
        "producto": "NDVI",
        "drew_geojson": "geojson_representation_of_AOI"
    }

Response:
    200 OK: The calculated geospatial product.
    400 Bad Request: Missing or invalid input data.
    500 Internal Server Error: Server error during processing.
