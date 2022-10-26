import datetime
import re

import min_renovasjon.const as c
import pytest
import requests
from min_renovasjon.minrenovasjon import MinRenovasjon


@pytest.fixture
def valid_address(requests_mock):
    search_string = "Jonas Lies gate 20, 2000 Lillestrøm"
    response = {
        "adresser": [
            {
                "adressekode": 7200,
                "adressenavn": "Jonas Lies gate",
                "kommunenavn": "LILLESTR\u00d8M",
                "kommunenummer": "3030",
                "nummer": 20,
                "postnummer": "2000",
                "poststed": "LILLESTR\u00d8M",
            }
        ]
    }
    requests_mock.get(c.ADDRESS_LOOKUP_URL, json=response)

    return MinRenovasjon._address_lookup(search_string), response


def test_municipality_is_app_customer():
    search_string = "Jonas Lies gate 20, 2000 Lillestrøm"
    ren = MinRenovasjon(search_string)

    assert ren.municipality_is_app_customer


def test_lookup_valid_address(valid_address):
    ren = valid_address[0]
    response = valid_address[1]

    assert ren[0] == response["adresser"][0]["adressenavn"]
    assert ren[1] == response["adresser"][0]["adressekode"]
    assert ren[2] == response["adresser"][0]["nummer"]
    assert ren[3] == response["adresser"][0]["kommunenavn"]
    assert ren[4] == response["adresser"][0]["kommunenummer"]
    assert ren[5] == response["adresser"][0]["postnummer"]
    assert ren[6] == response["adresser"][0]["poststed"]


def test_lookup_invalid_address(requests_mock):
    response = dict(adresser=[])
    requests_mock.get(c.ADDRESS_LOOKUP_URL, json=response)
    with pytest.raises(Exception) as e:
        MinRenovasjon._address_lookup("Gabla Habla 2224 Sotmo")
    assert "No address found for search string" in str(e.value)


def test_lookup_more_than_one_address(requests_mock):
    response = dict(adresser=[{}, {}])
    requests_mock.get(c.ADDRESS_LOOKUP_URL, json=response)
    with pytest.raises(Exception) as e:
        MinRenovasjon._address_lookup("Gabla Habla 2224 Sotmo")
    assert "Only one address should be returned." in str(e.value)


class MockRequestsError:
    def __init__(self, *args, **kwargs):
        raise requests.exceptions.RequestException


def test_lookup_address_with_exception(monkeypatch):
    monkeypatch.setattr("requests.get", MockRequestsError)
    with pytest.raises(SystemExit) as e:
        MinRenovasjon._address_lookup("Gabla Habla 2224 Sotmo")

    assert "RequestException" in str(e)


def test_base_request_with_exception(monkeypatch):
    monkeypatch.setattr("requests.get", MockRequestsError)
    with pytest.raises(SystemExit) as e:
        MinRenovasjon("Jonas Lies gate 20, 2000 Lillestrøm")


def test_municipality_not_customer(requests_mock):
    address_response = {
        "adresser": [
            {
                "adressekode": 24000,
                "adressenavn": "Storgata",
                "kommunenavn": "BOD\u00d8",
                "kommunenummer": "1804",
                "nummer": 92,
                "postnummer": "8006",
                "poststed": "BOD\u00d8",
            }
        ]
    }
    requests_mock.get(c.ADDRESS_LOOKUP_URL, json=address_response)

    # Mock customer lookup
    customer_response = [{"Number": "3030"}]
    requests_mock.get(c.APP_CUSTOMERS_URL, json=customer_response)

    with pytest.raises(Exception) as e:
        MinRenovasjon("Storgata 92, 8006 Bodø")

    assert "not a customer" in str(e.value)


@pytest.fixture(autouse=True)
def setup_minrenovasjon(requests_mock):
    # Address to use for mocking
    search_string = "Jonas Lies gate 20, 2000 Lillestrøm"

    # Mock address lookup
    address_response = {
        "adresser": [
            {
                "adressekode": 7200,
                "adressenavn": "Jonas Lies gate",
                "kommunenavn": "LILLESTR\u00d8M",
                "kommunenummer": "3030",
                "nummer": 20,
                "postnummer": "2000",
                "poststed": "LILLESTR\u00d8M",
            }
        ]
    }
    requests_mock.get(c.ADDRESS_LOOKUP_URL, json=address_response)

    # Mock customer lookup
    customer_response = [{"Number": "3030"}]
    requests_mock.get(c.APP_CUSTOMERS_URL, json=customer_response)

    # Mock fractions
    fractions = [
        {"Id": 1, "Navn": "Mat, plast og rest", "Ikon": ""},
        {"Id": 2, "Navn": "Papir", "Ikon": ""},
    ]
    requests_mock.get(c.KOMTEK_API_BASE_URL, json=fractions)

    # Mock waste collections
    collections_response = [
        {
            "FraksjonId": 1,
            "Tommedatoer": ["2020-04-17T00:00:00", "2020-04-24T00:00:00"],
        },
        {
            "FraksjonId": 2,
            "Tommedatoer": ["2020-04-20T00:00:00", "2020-05-18T00:00:00"],
        },
    ]

    requests_mock.get(re.compile(r"tommekalender"), json=collections_response)

    return MinRenovasjon(search_string)


class TestMinRenovasjon:
    def test_address_is_not_none(self, setup_minrenovasjon):
        address = setup_minrenovasjon
        assert address.street is not None
        assert address.number is not None
        assert address.municipality is not None
        assert address.municipality_code is not None

    def test_fractions(self, setup_minrenovasjon):
        assert len(setup_minrenovasjon.fractions) == 2

    def test_get_waste_collections(self, setup_minrenovasjon):
        assert setup_minrenovasjon.waste_collections is not None

    def test_waste_collection_has_date(self, setup_minrenovasjon):
        """dates should be instances of datetime.datetime"""

        for collection in setup_minrenovasjon.waste_collections:
            assert isinstance(collection.first_date, datetime.datetime)
            assert isinstance(collection.next_date, datetime.datetime)
