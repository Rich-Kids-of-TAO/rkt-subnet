import bittensor as bt
from typing import List, Dict, Tuple


def check_coldkey_wealth(
    subtensor,
    coldkey: str,
    balance_weight: float = 1.0,
    root_weight: float = 1.0,
    subnet_weight: float = 1.0,
    subnet_prices: dict = None,
    incentivize_low_price: bool = False,
) -> float:
    try:
        balance = subtensor.get_balance(coldkey)
        stake_info = subtensor.get_stake_for_coldkey(coldkey)

        netuid_totals = {}
        for info in stake_info:
            netuid = info.netuid
            stake_tao = info.stake.tao
            locked_tao = info.locked.tao

            if netuid not in netuid_totals:
                netuid_totals[netuid] = 0.0
            netuid_totals[netuid] += stake_tao + locked_tao

        total_stake_value = 0.0
        for netuid, stake_amount in netuid_totals.items():
            if netuid == 0:
                weight = root_weight
                stake_type = "Root"
            else:
                weight = subnet_weight
                stake_type = "Subnet"

            if subnet_prices and netuid in subnet_prices:
                price = subnet_prices[netuid]
                if price == 0.0:
                    weighted_value = 0.0
                else:
                    tao_value = stake_amount * price
                    if incentivize_low_price and price > 0:
                        bonus = 1.0 / price
                        weighted_value = tao_value * weight * bonus
                        bt.logging.info(
                            f"Netuid {netuid} ({stake_type}): {stake_amount:.4f} alpha * {price:.4f} price * {weight:.1f}x * {bonus:.4f} bonus = {weighted_value:.4f} TAO"
                        )
                    else:
                        weighted_value = tao_value * weight
                        bt.logging.info(
                            f"Netuid {netuid} ({stake_type}): {stake_amount:.4f} alpha * {price:.4f} price * {weight:.1f}x = {weighted_value:.4f} TAO"
                        )
            else:
                weighted_value = stake_amount * weight
                bt.logging.info(
                    f"Netuid {netuid} ({stake_type}): {stake_amount:.4f} (no price) * {weight:.1f}x = {weighted_value:.4f} TAO"
                )

            total_stake_value += weighted_value

        weighted_balance = balance.tao * balance_weight
        total_wealth = weighted_balance + total_stake_value

        total_wealth = max(0.0, total_wealth)

        bt.logging.info(
            f"Coldkey {coldkey}: Balance={balance.tao:.4f}*{balance_weight:.1f}x + Stakes={total_stake_value:.4f} = Total={total_wealth:.4f} TAO"
        )

        return total_wealth
    except Exception as e:
        bt.logging.warning(f"Could not get balance for coldkey {coldkey}: {e}")
        return 0.0


def check_uid_availability(metagraph, uid: int, vpermit_tao_limit: int = 1024) -> bool:
    if metagraph.validator_permit[uid]:
        if metagraph.S[uid] > vpermit_tao_limit:
            bt.logging.debug(
                f"UID {uid}: High-stake validator (stake: {metagraph.S[uid]:.2f})"
            )
            return False
    return True


def check_metagraph_wealth(
    validator_self,
    balance_weight: float = 1.0,
    root_weight: float = 1.0,
    subnet_weight: float = 1.0,
) -> Tuple[List[int], Dict[int, float]]:
    all_miner_uids = []
    miner_wealth = {}
    processed_coldkeys = set()

    for uid in range(validator_self.metagraph.n.item()):
        # Skip UID 0 (burner) unless we want to burn emissions
        if uid == 0 and validator_self.burner_weight == 0.0:
            bt.logging.debug(f"UID {uid}: Skipping burner UID (burn disabled)")
            continue

        uid_is_available = check_uid_availability(validator_self.metagraph, uid)

        if uid_is_available:
            coldkey = validator_self.metagraph.coldkeys[uid]

            if coldkey in processed_coldkeys:
                bt.logging.info(
                    f"UID {uid}: Skipping (coldkey {coldkey} already processed)"
                )
                miner_wealth[uid] = 0.0
                all_miner_uids.append(uid)
                continue

            processed_coldkeys.add(coldkey)
            all_miner_uids.append(uid)

            bt.logging.info(f"Checking UID {uid} with coldkey: {coldkey}")

            total_wealth = check_coldkey_wealth(
                validator_self.subtensor,
                coldkey,
                balance_weight,
                root_weight,
                subnet_weight,
                validator_self.subnet_prices,
                validator_self.incentivize_low_price,
            )
            miner_wealth[uid] = total_wealth

            bt.logging.info(f"UID {uid}: Total={total_wealth:.4f} TAO")
        else:
            bt.logging.debug(f"UID {uid}: Not available")

    bt.logging.info(
        f"Found {len(all_miner_uids)} available miners out of {validator_self.metagraph.n.item()} total UIDs"
    )
    bt.logging.info(f"Processed {len(processed_coldkeys)} unique coldkeys")
    return all_miner_uids, miner_wealth


def check_test_coldkeys_wealth(
    subtensor,
    test_coldkeys: List[str],
    balance_weight: float = 1.0,
    root_weight: float = 1.0,
    subnet_weight: float = 1.0,
    subnet_prices: dict = None,
    incentivize_low_price: bool = False,
) -> Tuple[List[int], Dict[int, float]]:
    all_miner_uids = []
    miner_wealth = {}

    for uid, coldkey in enumerate(test_coldkeys):
        bt.logging.info(f"Testing UID {uid} with coldkey: {coldkey}")
        all_miner_uids.append(uid)

        total_wealth = check_coldkey_wealth(
            subtensor,
            coldkey,
            balance_weight,
            root_weight,
            subnet_weight,
            subnet_prices,
            incentivize_low_price,
        )
        miner_wealth[uid] = total_wealth

        bt.logging.info(f"UID {uid}: Total={total_wealth:.4f} TAO")

    return all_miner_uids, miner_wealth


def get_rewards_from_wealth(wealth_values: List[float]):
    import numpy as np

    wealth_array = np.array(wealth_values, dtype=np.float32)

    if len(wealth_array) == 0:
        return np.array([])

    if np.all(wealth_array == 0):
        return np.ones_like(wealth_array) / len(wealth_array)

    max_wealth = np.max(wealth_array)
    if max_wealth > 0:
        normalized_rewards = wealth_array / max_wealth
    else:
        normalized_rewards = np.zeros_like(wealth_array)

    return normalized_rewards


def process_wealth_and_rewards(
    all_miner_uids: List[int], miner_wealth: Dict[int, float]
) -> Tuple[List[float], List[float]]:
    if not all_miner_uids:
        return [], []

    wealth_values = [miner_wealth.get(uid, 0.0) for uid in all_miner_uids]
    rewards = get_rewards_from_wealth(wealth_values)

    bt.logging.info(f"Wealth values: {[f'{w:.4f}' for w in wealth_values]}")
    bt.logging.info(f"Calculated rewards: {[f'{r:.6f}' for r in rewards]}")

    for uid, reward in zip(all_miner_uids, rewards):
        bt.logging.info(f"UID {uid}: Reward={reward:.4f}")

    return wealth_values, rewards
