from collections import namedtuple
from datetime import datetime
from typing import Dict, List, Tuple
import logging
import re

import requests

import minrenovasjon.constants as c

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

FractionCollections = namedtuple(
    "FractionCollections", "fraction_id, fraction_name, first_date, next_date"
)


class MinRenovasjon:
    def __init__(self, address_search_string: str):
        self.app_key = c.APP_KEY

        (
            self.street,
            self.street_code,
            self.number,
            self.municipality,
            self.municipality_code,
            self.postal_code,
            self.postal,
        ) = self._address_lookup(address_search_string)

        if self.municipality_is_app_customer:
            self.fractions = self._get_fractions()
        else:
            logger.info(f"{self.municipality} is not a customer of Min Renovasjon!")

    def _base_request(self, endpoint: str, params: dict = None) -> Dict:
        """
        Sets up the basic framework to make a call to the Komtek API.
        All API calls must go through a proxy server, hence both the base URL and separate endpoint url.

        :param endpoint: Desired endpoint to hit. Must include a trailing / if endpoint requires it.
        :param params: HTTP parameters to include in the request.
        :return: A dict with JSON results from the API.
        """
        url = c.KOMTEK_API_BASE_URL
        url_params = {"server": c.KOMTEK_API_ENDPOINT_URL + f"{endpoint}"}
        headers = {"RenovasjonAppKey": c.APP_KEY, "Kommunenr": self.municipality_code}
        if params:
            url_params.update(params)

        try:
            r = requests.get(url, headers=headers, params=url_params, timeout=3)
            r.raise_for_status()
        except requests.exceptions.RequestException as e:
            raise SystemExit(e)

        return r.json()

    def _get_fractions(self) -> Dict:
        """
        Get all fractions associated with the initialised address.
        Returned list dict of fractions includes all fractions available in this municipality.
        Not all these fractions are necessarily collected during waste collection.

        :return: Dict of all available fractions.
        """
        return self._base_request("fraksjoner/")

    def _get_waste_collections(self) -> Dict:
        """
        Gets waste collections from the Komtek API.
        The waste collections are grouped by fraction, and
        contains the two next collection dates.

        :return: Dict as returned from the API
        """
        params = {
            "gatenavn": self.street,
            "gatekode": f"{self.municipality_code}{self.street_code}",
            "husnr": self.number,
        }
        endpoint = f"tommekalender/?kommunenr={self.municipality_code}"
        return self._base_request(endpoint, params=params)

    @property
    def waste_collections(self) -> List:
        """
        Takes the waste collections returned by the Komtek API and maps the results
        to a list of FractionCollection named tuples.

        :return: List of FractionCollection named tuples
        """
        collections = self._get_waste_collections()

        _ = []

        for fraction in collections:
            _id = fraction["FraksjonId"]
            _name = [f["Navn"] for f in self.fractions if f["Id"] == _id][0]
            _first_date = self.to_datetime(fraction["Tommedatoer"][0])
            _next_date = self.to_datetime(fraction["Tommedatoer"][1])

            _.append(
                FractionCollections(
                    fraction_id=_id,
                    fraction_name=_name,
                    first_date=_first_date,
                    next_date=_next_date,
                )
            )

        return _

    @staticmethod
    def to_datetime(s: str, fmt: str = None) -> datetime:
        """
        Convert a string representing datetime to a datetime object either using
        the supplied format, or the normal datetime format provided by the Komtek API.

        :param s: String representing a datetime.
        :param fmt: Format of input string. Optional. Default value used if not set.
        :return: Datetime object
        """
        return datetime.strptime(s, fmt if fmt else "%Y-%m-%dT%H:%M:%S")

    @staticmethod
    def _address_lookup(s: str) -> Tuple:
        """
        Makes an API call to geonorge.no, the official resource for open geo data in Norway.
        This function is used to get deterministic address properties that is needed for
        further API calls with regards to Min Renovasjon, mainly municipality, municipality code,
        street name and street code.

        :param s: Search string for which address to search
        :return: Tuple of address fields
        """
        regex = r"(.*ve)(i|g)(.*)"
        subst = "\\1*\\3"

        search_string = re.sub(regex, subst, s, 0, re.MULTILINE)

        try:
            response = requests.get(
                c.ADDRESS_LOOKUP_URL,
                params={
                    "sok": search_string,
                    # Only get the relevant address fields
                    "filtrer": "adresser.kommunenummer,"
                    "adresser.adressenavn,"
                    "adresser.adressekode,"
                    "adresser.nummer,"
                    "adresser.kommunenavn,"
                    "adresser.postnummer,"
                    "adresser.poststed",
                },
            )
        except requests.exceptions.RequestException as e:
            raise SystemExit(e)

        data = response.json()
        logger.debug(data)

        if not data["adresser"]:
            raise Exception(f"No addresses found for search string '{s}'")

        if len(data["adresser"]) > 1:
            raise Exception(
                f"{len(data['adresser'])} addresses found. "
                f"Only one address should be returned. "
                f"Please narrow your search."
            )

        return (
            data["adresser"][0]["adressenavn"],
            data["adresser"][0]["adressekode"],
            data["adresser"][0]["nummer"],
            data["adresser"][0]["kommunenavn"],
            data["adresser"][0]["kommunenummer"],
            data["adresser"][0]["postnummer"],
            data["adresser"][0]["poststed"],
        )

    @property
    def municipality_is_app_customer(self) -> bool:
        """
        Make an API call to get all customers of the NorkartRenovasjon service which
        supports the Min Renovasjon app. Then check if this municipality is actually
        a customer or not.

        :return: Boolean indicating if this municipality is a customer or not.
        """
        try:
            response = requests.get(
                c.APP_CUSTOMERS_URL, params={"Appid": "MobilOS-NorkartRenovasjon"}
            )
        except requests.exceptions.RequestException as e:
            raise SystemExit(e)

        customers = response.json()
        return any(
            customer["Number"] == self.municipality_code for customer in customers
        )


def main() -> None:
    ren = MinRenovasjon("Norumveien 23 Sørum ")
    print(ren.waste_collections)


if __name__ == "__main__":
    main()
