import socket

import requests

API_ROOT = 'https://nominatim.openstreetmap.org'
import logging

logger = logging.getLogger(__name__)

DEG_ONE_KM = 0.009006575


def getGeoCode(house_number='', street='', city=''):
    """
    Returns latitude and longitude for a given address using the openstreetmap api.

    :param house_number: House number of the address.
    :param street: Street name of the address.
    :param city: City name of the address.
    :return: floats 'latitude, longitude' on success, 'none, none' on error.
    """
    # TODO: Blocking check
    try:
        url = "{api_root}/search?street={house_number} {street}&city={city}&country={country}&format=json" \
            .format(api_root=API_ROOT, house_number=house_number, street=street, city=city, country="Germany")
        response = requests.get(url=url, timeout=1)
        if response.json():
            latitude = response.json()[-1]['lat']
            longitude = response.json()[-1]['lon']
            return float(latitude), float(longitude)
    except socket.error as err:
        logger.error(err)
        pass
    return None, None


def getBoundingBox(latitude, longitude, distance):
    """
    Returns a bounding box around given position where distance was added in each direction.

    :return: min_lat, max_lat, min_lon, max_lon
    """
    distance_deg = float(distance) * DEG_ONE_KM
    return (latitude - distance_deg), (latitude + distance_deg), (longitude - distance_deg), (longitude + distance_deg)


if __name__ == "__main__":
    latitude, longitude = getGeoCode(36, "Margaretendamm", "Bamberg")
    print(latitude, longitude)
