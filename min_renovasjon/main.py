from collections import namedtuple
from datetime import datetime
from typing import Dict, List, Tuple
import logging
import re

import requests

import const as c

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

FractionCollection = namedtuple('WasteCollection', 'fraction_id, fraction_name, first_date, next_date')


class MinRenovasjon:

    def __init__(self, address_search_string: str, **kwargs):
        self.kwargs = kwargs
        self.app_key = c.APP_KEY

        (self.street,
         self.street_code,
         self.number,
         self.municipality,
         self.municipality_code,
         self.postal_code,
         self.postal) = self._address_lookup(address_search_string)

        if self.municipality_is_app_customer:
            self.fractions = self._get_fractions()
        else:
            logger.info(f"{self.municipality} is not a customer of Min Renovasjon!")

    def _base_request(self, endpoint: str, params: dict = None) -> Dict:
        url = c.KOMTEK_API_BASE_URL
        url_params = {'server': c.KOMTEK_API_ENDPOINT_URL + f"{endpoint}"}
        headers = {
            'RenovasjonAppKey': c.APP_KEY,
            'Kommunenr': self.municipality_code
        }
        if params:
            url_params.update(params)
        r = requests.get(url, headers=headers, params=url_params)
        return r.json()

    def _get_fractions(self) -> Dict:
        return self._base_request('fraksjoner/')

    def _get_waste_collections(self) -> Dict:
        params = {
            'gatenavn': self.street,
            'gatekode': f"{self.municipality_code}{self.street_code}",
            'husnr': self.number
        }
        endpoint = f"tommekalender/?kommunenr={self.municipality_code}"
        return self._base_request(endpoint, params=params)

    @property
    def waste_collections(self) -> List:
        collections = self._get_waste_collections()

        _ = []

        for fraction in collections:
            _id = fraction['FraksjonId']
            _name = [f['Navn'] for f in self.fractions if f['Id'] == _id][0]
            _first_date = self.to_datetime(fraction['Tommedatoer'][0])
            _next_date = self.to_datetime(fraction['Tommedatoer'][1])

            _.append(FractionCollection(fraction_id=_id,
                                        fraction_name=_name,
                                        first_date=_first_date,
                                        next_date=_next_date))

        return _

    @staticmethod
    def to_datetime(s: str) -> datetime:
        return datetime.strptime(s, '%Y-%m-%dT%H:%M:%S')

    @staticmethod
    def _address_lookup(s) -> Tuple:

        regex = r"(.*ve)(i|g)(.*)"
        subst = "\\1*\\3"

        search_string = re.sub(regex, subst, s, 0, re.MULTILINE)

        response = requests.get(c.ADDRESS_LOOKUP_URL,
                                params={
                                    'sok': search_string,
                                    # Only get the relevant address fields
                                    'filtrer': 'adresser.kommunenummer,'
                                               'adresser.adressenavn,'
                                               'adresser.adressekode,'
                                               'adresser.nummer,'
                                               'adresser.kommunenavn,'
                                               'adresser.postnummer,'
                                               'adresser.poststed'
                                })
        data = response.json()

        if len(data['adresser']) > 1:
            raise Exception(f"{len(data['adresser'])} addresses found. "
                            f"Only one address should be returned. "
                            f"Please narrow your search.")

        return (
            data['adresser'][0]['adressenavn'],
            data['adresser'][0]['adressekode'],
            data['adresser'][0]['nummer'],
            data['adresser'][0]['kommunenavn'],
            data['adresser'][0]['kommunenummer'],
            data['adresser'][0]['postnummer'],
            data['adresser'][0]['poststed']
        )

    @property
    def municipality_is_app_customer(self) -> bool:
        response = requests.get(c.APP_CUSTOMERS_URL, params={'Appid': 'MobilOS-NorkartRenovasjon'})
        customers = response.json()
        return any(customer['Number'] == self.municipality_code for customer in customers)


    ren = MinRenovasjon('Gamle Breviksvei 91, Porsgrunn')
def main() -> None:
    print(ren.municipality_is_app_customer)


if __name__ == '__main__':
    main()
