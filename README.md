# Rich Kids of TAO

The ultimate proof-of-wealth Bittensor subnet where your TAO balance is your talent.

## What is Rich Kids of TAO?

Rich Kids of TAO is a Bittensor subnet that rewards participants based on their TAO wealth. The more TAO you hold (liquid + staked), the higher your rewards.

## How it Works

- **Miners**: Simply register to the subnet - no code to run
- **Validators**: Check miners' coldkey TAO balances and distribute rewards accordingly
- **Rewards**: Based on total TAO wealth (liquid balance + staked assets)

## For Miners

1. Register your hotkey to the subnet:
```bash
btcli subnet register --netuid 110 --wallet.name YOUR_WALLET --wallet.hotkey YOUR_HOTKEY
```

2. That's it! Your rewards are based on your coldkey's TAO wealth.

## For Validators

1. Install dependencies:
```bash
pip install -e .
```

2. Run the validator:
```bash
pm2 start ./autoupdater.sh --name "rich-kids-autoupdater" -- 110 YOUR_WALLET YOUR_HOTKEY
```

## Testing

Test the wealth checking logic:
```bash
python test_wealth.py
```

## Wealth Calculation

Your score is based on:
- **Liquid TAO**: Balance in your coldkey
- **Root Stakes**: TAO staked in netuid 0 (Root subnet)  
- **Subnet Stakes**: TAO staked in other subnets

The validator applies configurable weights to each type and calculates relative rewards.

---

*Prove your wealth, earn your share.* 💰
