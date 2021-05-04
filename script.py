from functools import lru_cache
import csv
import requests
import pytz
from datetime import datetime


def get_orders(last_transaction_id: int, address: str) -> list:
    # TODO: Handle cursors.
    imx_url = "https://api.x.immutable.com/v1/orders"
    response = requests.get(imx_url + "?user=" +
                            address + "&status=filled&direction=asc").json()
    order_json = response["result"]
    valid_order_json = list(filter(
        lambda order: order["order_id"] >= last_transaction_id, order_json))
    orders = []
    wei_amount = 1000000000000000000
    for order in valid_order_json:
        is_buy_order = order["buy"]["type"] == "ERC721"
        if not is_buy_order:
            continue
        # Disregarding time for now.
        date = convert_utc_to_est(order["timestamp"].split(".")[0])
        coin_gecko_date = order["timestamp"].split("T")[0]
        eth_amount = int(order["amount_sold"]) / wei_amount
        card_name = order["buy"]["data"]["properties"]["name"]
        eth_price = get_eth_price("-".join(coin_gecko_date.split("-")[::-1]))
        orders.append([date, card_name, eth_amount, eth_price])

    return orders


def convert_utc_to_est(utc_datetime) -> str:
    est = pytz.timezone('US/Eastern')
    utc = pytz.utc
    fmt = '%m/%d/%Y %H:%M:%S'
    d = datetime.strptime(utc_datetime, "%Y-%m-%dT%H:%M:%S")
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
    rows = list(map(format_order, orders))
    return rows


def main():
    # TODO: add this as a console parameter
    last_transaction_id = 192845
    address = "0x1f4b9d5B19257e1496B907ef7b9284536f050499"

    orders = get_orders(last_transaction_id, address)
    rows = format_csv(orders)
    with open("data.csv", "w+") as my_csv:
        csvWriter = csv.writer(my_csv, delimiter=',')
        csvWriter.writerows(rows)


if __name__ == "__main__":
    main()
