import argparse
import numpy as np
import pandas as pd
from pyntcloud import PyntCloud

parser = argparse.ArgumentParser(description='Visualise the generated pointcloud.')
parser.add_argument('npz_file', type=str, help='Path to the points.npz file you want to visualise.')
args = parser.parse_args()

data = np.load(args.npz_file)
column_values = ["x", "y", "z"]

df = pd.DataFrame(data = data,
        columns = column_values) 