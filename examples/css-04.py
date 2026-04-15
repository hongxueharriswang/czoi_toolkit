# system4_epidemic.py
from datetime import timedelta
import random
from czoi.core import System, Zone, Role, User, Application
from czoi_toolkit.czoi.simulation.engine import SimulationEngine

# Zones
city1 = Zone("City1")
city2 = Zone("City2")
city3 = Zone("City3")
system = System()
for z in [city1, city2, city3]:
    system.add_zone(z)

# Roles
susceptible = Role("Susceptible", city1)  # will be zone-specific
infected = Role("Infected", city1)
recovered = Role("Recovered", city1)
vaccinated = Role("Vaccinated", city1)
official = Role("HealthOfficial", city1)
system.add_role(susceptible)
system.add_role(infected)
system.add_role(recovered)
system.add_role(vaccinated)
system.add_role(official)

# App
health_app = Application("Health")
travel_op = health_app.add_operation("travel")
quarantine_op = health_app.add_operation("quarantine")
vaccinate_op = health_app.add_operation("vaccinate")
report_op = health_app.add_operation("report_case")
system.add_application(health_app)

# Permissions: all can travel, only officials can report
for r in [susceptible, infected, recovered, vaccinated]:
    r.grant_permission(travel_op)
    r.grant_permission(quarantine_op)
    r.grant_permission(vaccinate_op)
official.grant_permission(report_op)

# Create population
population = []
for i in range(300):
    u = User(f"person_{i}")
    # assign to random city
    city = random.choice([city1, city2, city3])
    # initial health: most susceptible, few infected
    if i < 5:
        role = infected
        u.attributes["health_state"] = "I"
    else:
        role = susceptible
        u.attributes["health_state"] = "S"
    u.assign_role(city, role)
    u.attributes["compliance"] = random.uniform(0, 1)
    population.append(u)
    system.add_user(u)

# Officials
for i in range(3):
    off = User(f"official_{i}")
    off.assign_role(city1, official)
    off.attributes["health_state"] = "R"
    system.add_user(off)

# Infection parameters
beta = 0.3  # transmission rate
gamma = 0.1  # recovery rate

class EpidemicSim(SimulationEngine):
    def step(self, current_time):
        # For each city, count S,I,R
        for city in [city1, city2, city3]:
            users_in_city = [u for u in population if city.id in u.zone_role_assignments]
            s = [u for u in users_in_city if u.attributes["health_state"] == "S"]
            i = [u for u in users_in_city if u.attributes["health_state"] == "I"]
            # Infections
            num_infections = int(beta * len(s) * len(i) / max(1, len(users_in_city)))
            for _ in range(min(num_infections, len(s))):
                victim = random.choice(s)
                if victim.attributes["compliance"] > 0.5:  # high compliance reduces risk
                    if random.random() > 0.5:
                        continue
                victim.attributes["health_state"] = "I"
                # Update role: remove susceptible, add infected
                del victim.zone_role_assignments[city.id]
                victim.assign_role(city, infected)
                s.remove(victim)
            # Recoveries
            for infected_person in i:
                if random.random() < gamma:
                    infected_person.attributes["health_state"] = "R"
                    del infected_person.zone_role_assignments[city.id]
                    infected_person.assign_role(city, recovered)
            # Log
            self.logs.append({
                "timestamp": current_time.isoformat(),
                "city": city.name,
                "S": len(s),
                "I": len(i),
                "R": len([u for u in users_in_city if u.attributes["health_state"] == "R"])
            })

sim = EpidemicSim(system, None, None)
sim.run(timedelta(days=30), step=timedelta(days=1))
# Analyze final counts
for city in [city1, city2, city3]:
    users = [u for u in population if city.id in u.zone_role_assignments]
    s = sum(1 for u in users if u.attributes["health_state"] == "S")
    i = sum(1 for u in users if u.attributes["health_state"] == "I")
    r = sum(1 for u in users if u.attributes["health_state"] == "R")
    print(f"{city.name}: S={s}, I={i}, R={r}")