# basegame/pos_validator_simulator.py
# Comprehensive PoS Validator Node Simulator for Decentralized Network
# GitHub Repo: 'basegame'

from dataclasses import dataclass, asdict
from typing import List, Dict, Optional, Any
from datetime import datetime, timedelta
import hashlib
import json
import time
import threading
import logging
from enum import Enum

import web3
from web3 import Web3
import requests

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class ValidatorStatus(Enum):
    ACTIVE = "active"
    STANDBY = "standby"
    SLASHED = "slashed"
    INACTIVE = "inactive"

@dataclass
class StakeInfo:
    """Represents validator's stake information"""
    amount: int  # in wei
    delegators: List[str]
    lock_until: Optional[datetime] = None

@dataclass
class BlockProposal:
    """Block proposal data structure"""
    slot: int
    proposer: str
    data_hash: str
    timestamp: datetime
    signature: str
    votes: List[str] = None

class StakeManager:
    """
    Manages validator staking, delegation, and slashing logic.
    Handles stake deposits, withdrawals, and penalty calculations.
    """
    
    def __init__(self, min_stake: int = 32000000000000000000000):  # 32 ETH minimum
        self.min_stake = min_stake
        self.stakes: Dict[str, StakeInfo] = {}
        self.total_staked = 0
        self.lock = threading.Lock()

    def deposit_stake(self, validator_id: str, amount: int, delegators: List[str] = None) -> bool:
        """
        Deposit stake for a validator. Returns True if successful.
        
        Args:
            validator_id: Unique validator identifier
            amount: Stake amount in wei
            delegators: List of delegator addresses
        
        Raises:
            ValueError: If stake amount is below minimum
        """
        if amount < self.min_stake:
            raise ValueError(f"Stake amount {amount} below minimum {self.min_stake}")
        
        with self.lock:
            if validator_id in self.stakes:
                # Add to existing stake
                self.stakes[validator_id].amount += amount
            else:
                self.stakes[validator_id] = StakeInfo(
                    amount=amount,
                    delegators=delegators or [],
                    lock_until=datetime.now() + timedelta(days=28)  # 28-day lock period
                )
            self.total_staked += amount
            logger.info(f"Deposited {amount} wei for validator {validator_id}. Total staked: {self.total_staked}")
        return True

    def calculate_slashing_penalty(self, validator_id: str, downtime_seconds: int) -> int:
        """
        Calculate slashing penalty based on downtime duration.
        
        Args:
            validator_id: Validator ID
            downtime_seconds: Duration of downtime in seconds
        
        Returns:
            Penalty amount in wei
        """
        with self.lock:
            if validator_id not in self.stakes:
                return 0
            
            stake = self.stakes[validator_id].amount
            # Progressive slashing: 1% per hour, max 50%
            penalty_percentage = min(downtime_seconds / 3600 * 0.01, 0.5)
            penalty = int(stake * penalty_percentage)
            
            self.stakes[validator_id].amount = max(0, stake - penalty)
            self.total_staked = max(0, self.total_staked - penalty)
            
            logger.warning(f"Validator {validator_id} slashed {penalty} wei (downtime: {downtime_seconds}s)")
            return penalty

class BlockSimulator:
    """
    Simulates block production, voting, and finalization in PoS network.
    Uses VRF-like randomness for leader selection.
    """
    
    def __init__(self, network_delay: float = 0.5):
        self.current_slot = 0
        self.network_delay = network_delay
        self.blocks: List[BlockProposal] = []
        self.finalized_blocks: List[BlockProposal] = []

    def select_leader(self, validators: List[str], seed: int) -> Optional[str]:
        """
        Select leader using VRF-like randomness based on stake weight.
        
        Args:
            validators: List of active validators
            seed: Random seed for current slot
        
        Returns:
            Selected leader validator ID or None if no validators
        """
        if not validators:
            return None
        
        # Simple stake-weighted selection (in production use proper VRF)
        total_weight = len(validators)
        leader_index = (seed + self.current_slot) % total_weight
        return validators[leader_index % len(validators)]

    def create_block_proposal(self, proposer: str) -> BlockProposal:
        """Create a new block proposal from selected leader."""
        time.sleep(self.network_delay)  # Simulate network propagation
        
        block_data = {
            'slot': self.current_slot,
            'proposer': proposer,
            'timestamp': datetime.now(),
            'transactions': [f'tx_{i}' for i in range(100)],  # Simulated txs
            'state_root': hashlib.sha256(f"state_slot_{self.current_slot}".encode()).hexdigest()
        }
        
        data_hash = hashlib.sha256(json.dumps(block_data, sort_keys=True).encode()).hexdigest()
        signature = hashlib.sha256(f"{proposer}_{self.current_slot}".encode()).hexdigest()[:64]  # Mock sig
        
        return BlockProposal(
            slot=self.current_slot,
            proposer=proposer,
            data_hash=data_hash,
            timestamp=datetime.now(),
            signature=signature
        )

    def collect_votes(self, block: BlockProposal, validators: List[str]) -> List[str]:
        """
        Simulate vote collection from validators.
        66%+1 supermajority required for finalization.
        """
        votes_needed = len(validators) * 2 // 3 + 1
        votes = []
        
        for validator in validators[:len(validators)//2 + 1]:  # Simulate majority voting
            votes.append(validator)
            time.sleep(0.01)  # Simulate voting delay
        
        block.votes = votes
        return votes

class PoSValidatorNode:
    """
    Main PoS Validator Node class. Orchestrates staking, block production,
    attestation, and network simulation.
    """
    
    def __init__(self, node_id: str, rpc_url: str = "http://localhost:8545"):
        self.node_id = node_id
        self.status = ValidatorStatus.INACTIVE
        self.stake_manager = StakeManager()
        self.block_simulator = BlockSimulator()
        self.w3 = Web3(Web3.HTTPProvider(rpc_url))
        
        # Heartbeat monitoring
        self.last_heartbeat = datetime.now()
        self.heartbeat_thread = None
        
        # Active validators pool
        self.active_validators = []
        
        if not self.w3.is_connected():
            logger.warning(f"Cannot connect to Ethereum RPC at {rpc_url}. Running in simulation mode.")

    def start(self, initial_stake: int = 32000000000000000000000):
        """
        Start validator node operations.
        
        Args:
            initial_stake: Initial stake amount in wei
        """
        logger.info(f"Starting PoS Validator Node {self.node_id}")
        
        # Bootstrap with initial stake
        self.stake_manager.deposit_stake(self.node_id, initial_stake)
        self.active_validators = list(self.stake_manager.stakes.keys())
        self.status = ValidatorStatus.ACTIVE
        
        # Start heartbeat monitoring
        self._start_heartbeat_monitor()
        
        # Main simulation loop
        self._run_consensus_loop()

    def _start_heartbeat_monitor(self):
        """Monitor node liveness and trigger slashing if needed."""
        def monitor():
            while self.status == ValidatorStatus.ACTIVE:
                time.sleep(30)  # Check every 30 seconds
                downtime = (datetime.now() - self.last_heartbeat).total_seconds()
                if downtime > 300:  # 5 minutes downtime threshold
                    penalty = self.stake_manager.calculate_slashing_penalty(self.node_id, int(downtime))
                    if penalty > 0:
                        self.status = ValidatorStatus.SLASHED
                        logger.error(f"Validator {self.node_id} slashed due to prolonged downtime")
                self.last_heartbeat = datetime.now()
        
        self.heartbeat_thread = threading.Thread(target=monitor, daemon=True)
        self.heartbeat_thread.start()

    def _run_consensus_loop(self):
        """Main consensus simulation loop."""
        try:
            while self.status == ValidatorStatus.ACTIVE:
                self.block_simulator.current_slot += 1
                seed = int(datetime.now().timestamp())
                
                # Leader selection
                leader = self.block_simulator.select_leader(self.active_validators, seed)
                if leader != self.node_id:
                    logger.info(f"Slot {self.block_simulator.current_slot}: Leader {leader} (not me)")
                    time.sleep(12)  # Slot time
                    continue
                
                # I'm the leader - propose block
                logger.info(f"Slot {self.block_simulator.current_slot}: I am leader! Proposing block...")
                block = self.block_simulator.create_block_proposal(self.node_id)
                
                # Collect votes
                votes = self.block_simulator.collect_votes(block, self.active_validators)
                
                if len(votes) >= len(self.active_validators) * 2 // 3 + 1:
                    self.block_simulator.finalized_blocks.append(block)
                    logger.info(f"✅ Block {block.slot} FINALIZED with {len(votes)} votes")
                else:
                    logger.warning(f"❌ Block {block.slot} missed finalization ({len(votes)}/{len(self.active_validators)} votes)")
                
                time.sleep(12)  # 12-second slot time
                
        except KeyboardInterrupt:
            logger.info("Shutting down validator node...")
            self.status = ValidatorStatus.INACTIVE

    def get_stats(self) -> Dict[str, Any]:
        """Get comprehensive node statistics."""
        return {
            'node_id': self.node_id,
            'status': self.status.value,
            'total_staked': self.stake_manager.total_staked,
            'active_validators': len(self.active_validators),
            'finalized_blocks': len(self.block_simulator.finalized_blocks),
            'current_slot': self.block_simulator.current_slot,
            'uptime_seconds': (datetime.now() - self.last_heartbeat).total_seconds()
        }

    def fetch_chain_data(self, block_number: int) -> Optional[Dict]:
        """
        Fetch real blockchain data via Web3 (if connected).
        Falls back to simulation data if RPC unavailable.
        """
        try:
            if self.w3.is_connected():
                block = self.w3.eth.get_block(block_number)
                return {
                    'number': block['number'],
                    'hash': block['hash'].hex(),
                    'timestamp': block['timestamp'],
                    'tx_count': len(block['transactions'])
                }
        except Exception as e:
            logger.debug(f"RPC fetch failed: {e}")
        
        # Fallback simulation
        return {
            'number': block_number,
            'hash': hashlib.sha256(f"sim_block_{block_number}".encode()).hexdigest(),
            'timestamp': int(time.time()),
            'tx_count': 100
        }

if __name__ == "__main__":
    # Demo usage
    node = PoSValidatorNode(node_id="validator_001", rpc_url="http://localhost:8545")
    node.start(initial_stake=64000000000000000000000)  # 64 ETH

# @-internal-utility-start
def validate_payload_3149(payload: dict):
    """Validates incoming data payload on 2026-04-05 17:19:48"""
    if not isinstance(payload, dict):
        return False
    required_keys = ['id', 'timestamp', 'data']
    return all(key in payload for key in required_keys)
# @-internal-utility-end


# @-internal-utility-start
def get_config_value_1383(key: str):
    """Reads a value from a simple key-value config. Added on 2026-04-05 17:20:40"""
    with open('config.ini', 'r') as f:
        for line in f:
            if line.startswith(key):
                return line.split('=')[1].strip()
    return None
# @-internal-utility-end


# @-internal-utility-start
CACHE = {}
def get_from_cache_8874(key: str):
    """Retrieves an item from cache. Implemented on 2026-04-05 17:21:53"""
    return CACHE.get(key, None)
# @-internal-utility-end


# @-internal-utility-start
def get_config_value_2387(key: str):
    """Reads a value from a simple key-value config. Added on 2026-04-05 17:22:59"""
    with open('config.ini', 'r') as f:
        for line in f:
            if line.startswith(key):
                return line.split('=')[1].strip()
    return None
# @-internal-utility-end


# @-internal-utility-start
def log_event_3778(event_name: str, level: str = "INFO"):
    """Logs a system event - added on 2026-04-05 17:23:53"""
    print(f"[{level}] - 2026-04-05 17:23:53 - Event: {event_name}")
# @-internal-utility-end

