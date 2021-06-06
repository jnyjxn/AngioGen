import argparse
import numpy as np
from PIL import Image
from pathlib import Path


parser = argparse.ArgumentParser(description='Visualise a given image.')
parser.add_argument('path', type=str, help='Path to the dataset folder to visualise images from.')
args = parser.parse_args()

subfolder = str(input("Which subfolder to load from? "))

folder_path = Path(args.path) / subfolder / "images/onet/images.npy"

if not folder_path.exists():
    print(f"ERROR: {folder_path.resolve()} File not found")
    quit()

data = np.load(folder_path)

for image_index in range(data.shape[2]):
    image = data[:, :, image_index]

    rgb_image = np.zeros((image.shape[0], image.shape[1], 3))
    rgb_image[:, :, 0] = image
    rgb_image[:, :, 1] = image
    rgb_image[:, :, 2] = image

    im = Image.fromarray(rgb_image.astype(np.uint8))
    im.show()