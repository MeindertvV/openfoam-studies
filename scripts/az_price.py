#!/usr/bin/env python3
"""Print de actuele Linux-uurprijs in euro van een VM uit de openbare Azure-prijslijst.

Gebruik: az_price.py <VM-type> <regio> [--spot]
Exit 1 als de prijs niet te vinden is.
"""
import json
import sys
import urllib.parse
import urllib.request

API = "https://prices.azure.com/api/retail/prices?currencyCode=EUR&$filter="


def fetch(size, region):
    query = (f"serviceName eq 'Virtual Machines' and armRegionName eq '{region}' "
             f"and armSkuName eq '{size}' and priceType eq 'Consumption'")
    url = API + urllib.parse.quote(query)
    with urllib.request.urlopen(url, timeout=30) as response:
        return json.load(response)["Items"]


def select(items, spot):
    """Kies de Linux-prijs; Windows en Low Priority tellen niet mee."""
    for item in items:
        if "Windows" in item["productName"] or "Low Priority" in item["skuName"]:
            continue
        if ("Spot" in item["skuName"]) == spot:
            return item["retailPrice"]
    return None


def main():
    if len(sys.argv) not in (3, 4):
        sys.exit("gebruik: az_price.py <VM-type> <regio> [--spot]")
    price = select(fetch(sys.argv[1], sys.argv[2]), "--spot" in sys.argv[3:])
    if price is None:
        sys.exit(f"FOUT: geen prijs voor {sys.argv[1]} in {sys.argv[2]}")
    print(price)


if __name__ == "__main__":
    main()
