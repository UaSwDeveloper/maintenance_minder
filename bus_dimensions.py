from faker import Faker
import pandas as pd
import random

# Instantiate a Faker object
fake = Faker()

# Define possible regions
regions = ['Northern', 'Southern', 'Eastern', 'Western', 'Central']
def get_bus_dimensions(bus_ids):
    # Generate a list of unique states and vendors
    states = [fake.state() for _ in range(8)]
    vendors = [fake.company() for _ in range(7)]

    # Generate fake data for each bus_id
    data = []
    for bus_id in bus_ids:
        state = random.choice(states)
        bus_vendor = random.choice(vendors)
        region = random.choice(regions)
        data.append([bus_id, state, bus_vendor, region])


    # Create a DataFrame
    df = pd.DataFrame(data, columns=['bus_id', 'state', 'bus_vendor', 'region'])
    return df