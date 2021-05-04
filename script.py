from functools import lru_cache
import csv
import requests


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
        date = order["timestamp"].split("T")[0]
        eth_amount = int(order["amount_sold"]) / wei_amount
        card_name = order["buy"]["data"]["properties"]["name"]
        eth_price = get_eth_price("-".join(date.split("-")[::-1]))
        orders.append([date, card_name, eth_amount, eth_price])

    return orders


@lru_cache
def get_eth_price(date: str) -> int:
    url = "http://api.coingecko.com/api/v3/coins/ethereum/history"
    response = requests.get(url + "?date=" + date)
    return response.json()["market_data"]["current_price"]["cad"]


def format_csv(orders: list):
    def format_order(order):
        date, card_name, eth_amount, eth_price = order
        return [date, "imx buy", "$" + str(eth_price), 0, 0, card_name, "M", eth_amount]
    rows = list(map(format_order, orders))
    return rows


def main():
    # TODO: add this as a console parameter
    last_transaction_id = 192845
    address = "0x1f4b9d5B19257e1496B907ef7b9284536f050499"

    orders = get_orders(last_transaction_id, address)
    rows = format_csv(orders)
    print(rows)


if __name__ == "__main__":
    main()
