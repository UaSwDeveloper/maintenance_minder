from copy import deepcopy
import numpy as np
import pandas as pd
from datetime import datetime, timedelta
import random

np.random.seed(0)

# School bus mileage per day is ~63.4 miles
# https://calstart.org/wp-content/uploads/2021/12/Electric-School-Bus-Market-Report-2021.pdf
# https://www.nysbca.com/fastfacts
avg_mileage_per_day = 63.4
standard_mileages = {
    'engine': 500_000,
    'transmission': 1_000_000,
    'radiator': 100_000,
    'breaks': 100_000
}

def generate_bus_history(bus_id: int, 
                         first_timestamp: datetime, 
                         component_to_replace: np.array):
    """


    Parameters
    ----------
    bus_id : int
        Bus ID.
    first_timestamp : datetime
        First timestamp of the history.
    component_to_replace : np.array
        n x m matrix where n is ``history_size`` and m - number of bus components
        like engine, transmission,radiator etc. Values in the matrix are either 0 or 1.

    incident_probability : np.array
        1 x m array where m - number of bus components like engine, transmission,radiator etc.
        Values in the array are probabilities of incident for each component. The higher chance,
        the less time component will work -> less mileage.
    
    Returns
    -------
    np.array
        Generated history.
    """
    def _increase_next_row(matrix):
        """
        A helper function that accumylate changes overtime:
        array([[1., 0., 0., 0.],         array([[1., 0., 0., 0.],
               [0., 1., 0., 0.],                [1., 1., 0., 0.],
               [0., 0., 1., 0.],                [1., 1., 1., 0.],
               [0., 0., 0., 1.],                [1., 1., 1., 1.],
               [0., 0., 1., 0.],       ->       [1., 1., 2., 1.],
               [1., 1., 0., 0.],                [2., 2., 2., 1.],
               [1., 0., 0., 0.],                [3., 2., 2., 1.],
               [0., 1., 0., 0.],                [3., 3., 2., 1.],
               [0., 0., 1., 0.],                [3., 3., 3., 1.],
               [1., 0., 0., 0.]])               [4., 3., 3., 1.]])

        """
        result_matrix = deepcopy(matrix)
        for i in range(matrix.shape[0]):
            result_matrix[i:] += matrix[i]
        result_matrix = result_matrix - matrix
        return result_matrix
    #
    # Adding init record
    zeros = np.zeros(component_to_replace.shape[1])
    components_history = np.vstack((zeros, component_to_replace))
    component_ids = _increase_next_row(components_history)
    #
    np.random.seed(0)
    mileage_coefficients = np.random.normal(1, 0.2, component_to_replace.shape)
    mileages_matrix = mileage_coefficients * np.array(list(standard_mileages.values()))
    # Replace zeros with infinities
    mileages_matrix[mileages_matrix == 0] = np.inf
    mileages = _increase_next_row(np.min(mileages_matrix, axis=1).reshape(-1, 1))
    mileages = mileages.astype(np.int32)
    # add zero as the first row in the mileage matrix
    mileages = np.vstack((np.zeros((1, 1)), mileages))
    days_to_add = (mileages[1:] / avg_mileage_per_day).astype(np.int32)
    start_timestamps = [first_timestamp] + [first_timestamp + timedelta(days=int(days[0])) 
                                            for days in days_to_add]
    start_timestamps = np.array(start_timestamps).reshape(-1, 1)
    end_timestamps = [first_timestamp + timedelta(days=int(days[0])-1) 
                      for days in days_to_add] + [None]
    end_timestamps = np.array(end_timestamps).reshape(-1, 1)
    bus_id_col = np.full((component_ids.shape[0], 1), bus_id)
    result = np.hstack((bus_id_col, 
                        component_ids, 
                        mileages,
                        start_timestamps,
                        end_timestamps))
    return result

def get_components_to_replace():
    component_to_replace = np.array([[1., 0., 0., 0.],
                                     [0., 1., 0., 0.],
                                     [0., 0., 1., 0.],
                                     [0., 0., 0., 1.],
                                     [0., 0., 1., 0.],
                                     [1., 1., 0., 0.],
                                     [1., 0., 0., 0.],
                                     [0., 1., 0., 0.],
                                     [0., 0., 1., 0.],
                                     [1., 0., 0., 0.]])
    component_to_replace_copy = np.copy(component_to_replace)
    np.random.shuffle(component_to_replace_copy)
    return component_to_replace_copy


def _get_random_datetime(start_date, end_date):
    # start_date = datetime(2000, 3, 17)
    # end_date = datetime(2001, 2, 8)
    random_date = start_date + timedelta(
        days=random.randint(0, (end_date - start_date).days))
    return random_date

def get_bus_history_data(n_buses=1):

    bus_ids = list(range(1, n_buses+1))
    np_arrays = []
    components = []
    for bus_id in bus_ids:
        # start = datetime(2000, 7, 13)
        start = _get_random_datetime(datetime(2000, 3, 17), datetime(2001, 2, 8))  
        component_to_replace = get_components_to_replace()

        h = generate_bus_history(bus_id, start, component_to_replace)
        component_id_shiter = bus_id * 1000
        h[:, 1:5] = h[:, 1:5] + component_id_shiter
        np_arrays.append(h)
        components.append(component_to_replace)
    columns = ['bus_id', 
                'engine_id',
                'transmission_id',
                'radiator_id',
                'breaks_id',
                'mileage', 
                'start_timestamp', 
                'end_timestamp']
    return pd.DataFrame(np.vstack(np_arrays), columns=columns), np.vstack(components)
