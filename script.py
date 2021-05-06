from functools import lru_cache
import csv
import requests
import pytz
from datetime import datetime
import urllib.parse
import sys


def get_orders(last_transaction_id: int, address: str) -> list:
    filtered_orders = get_order_json(last_transaction_id, address)
    orders = []
    wei_amount = 1000000000000000000
    for order in filtered_orders:
        # Part after the . is Z value, so I am just disregarding it.
        date = convert_utc_to_est(order["timestamp"].split(".")[0])
        coin_gecko_date = order["timestamp"].split("T")[0]
        eth_amount = int(order["amount_sold"]) / wei_amount
        card_name = order["buy"]["data"]["properties"]["name"]
        eth_price = get_eth_price("-".join(coin_gecko_date.split("-")[::-1]))
        orders.append([date, card_name, eth_amount, eth_price])

    return orders


def get_order_json(last_transaction_id: int, address: str) -> dict:
    imx_url = "https://api.x.immutable.com/v1/orders?"
    raw_orders = []
    cursor = ""
    firstTime = True
    while firstTime or len(cursor) > 0:
        firstTime = False
        parameters = {"user": address, "status": "filled",
                      "direction": "asc"}
        if len(cursor) > 0:
            parameters["cursor"] = cursor
        response = requests.get(
            imx_url + urllib.parse.urlencode(parameters)).json()
        raw_orders += response["result"]
        cursor = response["cursor"]

    filtered_orders = list(filter(
        lambda order: order["buy"]["type"] == "ERC721" and order["order_id"] >= last_transaction_id,
        raw_orders))
    return filtered_orders


def convert_utc_to_est(utc_datetime: str) -> str:
    est = pytz.timezone('US/Eastern')
    utc = pytz.utc
    fmt = '%m/%d/%Y %H:%M:%S'
    d = datetime.strptime(utc_datetime, "%Y-%m-%dT%H:%M:%S")
    # This was done as I couldn't figure out another way to add tzinfo to d.
    d = datetime(d.year, d.month, d.day, d.hour,
                 d.minute, d.second, tzinfo=utc)
    return str(d.astimezone(utc).astimezone(est).strftime(fmt))


@lru_cache
def get_eth_price(date: str) -> int:
    url = "http://api.coingecko.com/api/v3/coins/ethereum/history"
    response = requests.get(url + "?date=" + date)
    return response.json()["market_data"]["current_price"]["cad"]


def format_csv(orders: list):
    def format_order(order):
        date, card_name, eth_amount, eth_price = order
        return [date, "imx buy", "$" + str(eth_price), 0,
                0, card_name, "M", eth_amount]
    header = ["Buy Date", "Type", "ETH Buy Unit Price",
              "Buy Fee", "Amount", "Card Name", "Quality", "Cost Basis"]
    rows = [header] + list(map(format_order, orders))
    return rows


def main():
    n = len(sys.argv)
    if n != 2:
        print("Error, must have exactly one argument: Last Transaction Id.")
        return
    last_transaction_id = -1
    try:
        last_transaction_id = int(sys.argv[1])
    except:
        print("Error: Last Transaction Id must be an integer")
        return

    address = "0x1f4b9d5B19257e1496B907ef7b9284536f050499"

    orders = get_orders(last_transaction_id, address)
    rows = format_csv(orders)
    with open("data.csv", "w+") as my_csv:
        csvWriter = csv.writer(my_csv, delimiter=',')
        csvWriter.writerows(rows)


if __name__ == "__main__":
    main()
