# system3_market.py
from datetime import timedelta
import random
import numpy as np
from czoi.core import System, Zone, Role, User, Application
from czoi_toolkit.czoi.simulation.engine import SimulationEngine

# Zones
exchange = Zone("Exchange")
mm_desk = Zone("MarketMakerDesk", parent=exchange)
arb_desk = Zone("ArbitrageDesk", parent=exchange)
noise_desk = Zone("NoiseDesk", parent=exchange)
system = System()
for z in [exchange, mm_desk, arb_desk, noise_desk]:
    system.add_zone(z)

# Roles
market_maker = Role("MarketMaker", exchange)
arbitrageur = Role("Arbitrageur", exchange)
noise_trader = Role("NoiseTrader", exchange)
system.add_role(market_maker)
system.add_role(arbitrageur)
system.add_role(noise_trader)

# App
trading_app = Application("Trading")
place_op = trading_app.add_operation("place_order")
cancel_op = trading_app.add_operation("cancel_order")
quote_op = trading_app.add_operation("get_quote")
system.add_application(trading_app)

# Permissions (all can place orders)
for r in [market_maker, arbitrageur, noise_trader]:
    r.grant_permission(place_op)
    r.grant_permission(cancel_op)
    r.grant_permission(quote_op)

# Create traders
traders = []
for i in range(5):
    u = User(f"mm_{i}")
    u.assign_role(mm_desk, market_maker)
    u.attributes["cash"] = 100000
    u.attributes["holdings"] = 0
    u.attributes["risk_tolerance"] = 0.2
    traders.append(u)
    system.add_user(u)

for i in range(3):
    u = User(f"arb_{i}")
    u.assign_role(arb_desk, arbitrageur)
    u.attributes["cash"] = 50000
    u.attributes["holdings"] = 0
    u.attributes["risk_tolerance"] = 0.5
    traders.append(u)
    system.add_user(u)

for i in range(10):
    u = User(f"noise_{i}")
    u.assign_role(noise_desk, noise_trader)
    u.attributes["cash"] = 10000
    u.attributes["holdings"] = 0
    u.attributes["risk_tolerance"] = 0.8
    traders.append(u)
    system.add_user(u)

# Price state
price = 100.0

class MarketSim(SimulationEngine):
    def __init__(self, initial_price):
        super().__init__()
        self.price = initial_price

    def step(self, current_time):
        # Generate orders randomly
        # Example price update
        self.price += 0.1

        # Generate orders randomly
        for u in traders:
            if random.random() < 0.3:
                # decide buy/sell based on role
                if "mm" in u.username:
                    # market maker provides liquidity
                    side = random.choice(["buy", "sell"])
                elif "arb" in u.username:
                    # arbitrageur follows trend
                    side = "buy" if random.random() > 0.5 else "sell"
                else:
                    # noise trader random
                    side = random.choice(["buy", "sell"])
                quantity = random.randint(1, 10)
                # Simulate price impact
                if side == "buy":
                    price *= 1 + 0.001 * quantity
                else:
                    price *= 1 - 0.001 * quantity
                self.logs.append({
                    "timestamp": current_time.isoformat(),
                    "trader": u.username,
                    "side": side,
                    "quantity": quantity,
                    "price": price
                })
        # Enforce constraints: cash/holdings not implemented for brevity

sim = MarketSim(system, None, None)
sim.run(timedelta(minutes=10), step=timedelta(seconds=1))
print(f"Final price: {price:.2f}")