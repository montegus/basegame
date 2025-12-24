# basegame - PoS Validator Node Simulator

[![Python](https://img.shields.io/badge/python-3.8%2B-blue.svg)](https://www.python.org/downloads/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

**Production-grade Proof-of-Stake (PoS) Validator Node Simulator** for Ethereum-like networks. This is a comprehensive simulation of a validator node in a decentralized PoS blockchain network, including staking management, block proposal, voting, slashing, heartbeat monitoring, and Web3 integration.

## Concept

This project simulates a **PoS Validator Node** in a decentralized blockchain network with the following core features:

- **Stake Management**: Handles deposits, delegations, lock periods, and progressive slashing
- **Leader Election**: VRF-like randomness for slot leader selection
- **Block Production**: Simulates block proposal with realistic network delays
- **Consensus**: 66%+1 supermajority voting for block finalization
- **Slashing**: Automatic penalties for downtime/misbehavior
- **Monitoring**: Heartbeat system with uptime tracking
- **Web3 Integration**: Real Ethereum RPC connectivity with fallback simulation
- **Production Architecture**: Threading, logging, error handling, type hints

The simulator models real-world PoS dynamics like Ethereum 2.0, including 12-second slot times, 32 ETH minimum stake, and 28-day withdrawal delays.

## Code Architecture

```
PoSValidatorNode (Main Orchestrator)
├── StakeManager
│   ├── deposit_stake()
│   ├── calculate_slashing_penalty()
│   └── Thread-safe stake tracking
├── BlockSimulator
│   ├── select_leader() - VRF randomness
│   ├── create_block_proposal()
│   └── collect_votes() - 66%+1 finality
├── Web3 Integration
└── Heartbeat Monitor (Threaded)
```

**Key Design Patterns**:
- **Data Classes** for immutable structures
- **Threading** for concurrent monitoring
- **Progressive Slashing** (1% per hour downtime)
- **Fallback Simulation** when RPC unavailable
- **Comprehensive Logging** and error handling

## How it Works

1. **Bootstrap**: Node deposits minimum stake (32+ ETH) and joins active validator set
2. **Slot Loop** (12s intervals):
   - VRF selects slot leader
   - Leader proposes block with tx batch
   - Validators vote (simulated 66%+1)
   - Block finalizes or misses
3. **Monitoring**: Heartbeat checks every 30s, slashes after 5min downtime
4. **Web3 Bridge**: Fetches real chain data when RPC available

**Slashing Formula**: `penalty = stake × min(downtime_hours × 0.01, 0.5)`

## Features

- ✅ **Stake-weighted leader election**
- ✅ **Realistic block production** (100 txs/block)
- ✅ **Progressive slashing mechanism**
- ✅ **66%+1 finality consensus**
- ✅ **Web3 Ethereum integration**
- ✅ **Thread-safe operations**
- ✅ **Production logging**
- ✅ **Edge case handling**
- ✅ **Graceful RPC fallbacks**

## Usage Example

```bash
# 1. Install dependencies
pip install -r requirements.txt

# 2. Run validator node (64 ETH stake)
python pos_validator_simulator.py

# Output:
# 2024-01-15 10:30:01 - INFO - Starting PoS Validator Node validator_001
# 2024-01-15 10:30:01 - INFO - Deposited 64000000000000000000000 wei for validator validator_001
# 2024-01-15 10:30:13 - INFO - Slot 1: Leader validator_001 (I am leader!) Proposing block...
# 2024-01-15 10:30:14 - INFO - ✅ Block 1 FINALIZED with 2 votes
```

### Programmatic Usage

```python
from pos_validator_simulator import PoSValidatorNode

node = PoSValidatorNode("my_node")
node.start(initial_stake=32_000_000_000_000_000_000_000)  # 32 ETH

# Get stats
print(node.get_stats())

# Fetch real chain data
block_data = node.fetch_chain_data(12345678)
print(block_data)
```

## Production Deployment

```bash
# Docker (recommended)
docker build -t pos-validator .
docker run -p 8545:8545 pos-validator

# With real Ethereum node
RPC_URL="https://mainnet.infura.io/v3/YOUR_KEY" python pos_validator_simulator.py
```

## Error Handling & Edge Cases

- **Low stake**: `ValueError` on deposits < 32 ETH
- **RPC failure**: Automatic simulation fallback
- **No active validators**: Skip slot gracefully
- **Network partition**: Simulated delays and timeouts
- **Double-spend attempts**: Hash validation in blocks
- **Validator slashing**: Progressive penalties up to 50%

## Requirements

See `requirements.txt` for pinned versions.

## License

MIT License - see `LICENSE` file for details.

---

**Built for 'basegame' repository** - Production-ready PoS validator simulation.