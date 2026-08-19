"""Search the API marketplace and price an endpoint — no wallet, no payment.

Searching and reading prices are free; only invoking an endpoint is billed. So
this runs end to end without a key or a wallet, and stops just short of
spending: it prints the quote instead of paying it.

    python examples/05_marketplace.py

Point it at any AIP-compatible gateway with AIP_ENDPOINT:

    AIP_ENDPOINT=https://your-gateway.example python examples/05_marketplace.py

To actually call an endpoint, give the client a wallet and use call_api — see
03_execute_with_wallet.py for the wallet setup.
"""

import os

from agent_intent_protocol import AIPClient, AIPPaymentRequiredError


def main() -> None:
    endpoint = os.getenv("AIP_ENDPOINT")
    client = AIPClient(endpoint=endpoint) if endpoint else AIPClient()

    with client:
        # How large is the catalogue, and how is it split up?
        catalogue = client.search_apis()
        print(f"{catalogue.total} endpoints across {len(catalogue.categories)} categories")
        for c in catalogue.categories[:6]:
            print(f"  {c.get('category'):<12} {c.get('count')}")

        # Free-text search. `total` is the number of matches in the catalogue,
        # which is not the same as the number returned on this page.
        hits = client.search_apis("weather", page_size=5)
        print(f"\n'weather' matches {hits.total}; first {len(hits)}:")
        for api in hits:
            price = f"${api.display_price}/{api.price_unit}" if api.display_price else "n/a"
            print(f"  {api.name:<28} {price:<16} {api.path}")

        if not len(hits):
            print("\nNo matches — nothing to price.")
            return

        # Read one entry in full before deciding to pay for it.
        first = hits.items[0]
        detail = client.get_api(first.slug or first.resource_id)
        print(f"\n{detail.name}: {detail.method} {detail.path}")
        print(f"  category={detail.category}  price={detail.display_price} per {detail.price_unit}")

        # Without a wallet the paid call surfaces the quote rather than
        # settling, so you can see the terms on every supported chain.
        try:
            # Passing the entry itself uses the verb the catalogue publishes
            # for it — 45% of the catalogue is GET.
            client.call_api(detail)
        except AIPPaymentRequiredError as exc:
            body = exc.body if isinstance(exc.body, dict) else {}
            accepts = body.get("accepts") or []
            print(f"\nQuote carries {len(accepts)} payment option(s):")
            for a in accepts:
                print(f"  {a.get('network'):<44} -> {a.get('payTo')}")
            print("\nAdd a Wallet and the same call signs and settles automatically.")


if __name__ == "__main__":
    main()
