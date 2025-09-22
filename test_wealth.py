import bittensor as bt
from rich_kids_of_tao.wealth_checker import (
    check_test_coldkeys_wealth,
    process_wealth_and_rewards,
)


def main():
    bt.logging.set_debug(True)
    bt.logging.set_trace(True)

    bt.logging.info("=== Rich Kids of TAO Test Runner ===")

    test_coldkeys = [
    ]

    try:
        subtensor = bt.subtensor(network="finney")
        bt.logging.info("Connected to subtensor")
    except Exception as e:
        bt.logging.error(f"Failed to connect to subtensor: {e}")
        return

    bt.logging.info("Fetching subnet prices for test...")
    try:
        all_subnets = subtensor.all_subnets()
        subnet_prices = {}
        for subnet in all_subnets:
            netuid = subnet.netuid
            if subnet.alpha_out_emission == 0.0:
                subnet_prices[netuid] = 0.0
                bt.logging.debug(f"Netuid {netuid}: Inactive, price = 0.0")
            else:
                try:
                    price = subtensor.get_subnet_price(netuid=netuid)
                    subnet_prices[netuid] = price.tao
                    bt.logging.debug(
                        f"Netuid {netuid}: Active, price = {price.tao:.4f}"
                    )
                except:
                    subnet_prices[netuid] = 1.0
        bt.logging.info(f"Fetched prices for {len(subnet_prices)} subnets")
    except Exception as e:
        bt.logging.error(f"Failed to fetch subnet prices: {e}")
        subnet_prices = None

    bt.logging.info("=== Testing wealth checking with hardcoded coldkeys ===")

    BALANCE_WEIGHT = 1.0
    ROOT_WEIGHT = 1.0
    SUBNET_WEIGHT = 1.0

    bt.logging.info(
        f"Using weights - Balance: {BALANCE_WEIGHT:.1f}x, Root: {ROOT_WEIGHT:.1f}x, Subnets: {SUBNET_WEIGHT:.1f}x"
    )

    all_miner_uids, miner_wealth = check_test_coldkeys_wealth(
        subtensor,
        test_coldkeys,
        BALANCE_WEIGHT,
        ROOT_WEIGHT,
        SUBNET_WEIGHT,
        subnet_prices,
        False,
    )

    if not all_miner_uids:
        bt.logging.info("No test miners found")
        return

    wealth_values, rewards = process_wealth_and_rewards(all_miner_uids, miner_wealth)

    bt.logging.info("=== Test Results Summary ===")
    for i, uid in enumerate(all_miner_uids):
        bt.logging.info(
            f"UID {uid}: Wealth={miner_wealth[uid]:.4f} TAO, Reward={rewards[i]:.4f}"
        )

    bt.logging.info("=== Test Complete ===")


if __name__ == "__main__":
    main()
