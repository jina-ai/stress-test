import gzip
import os
from read_vectors_files import fvecs_read

DATA_DIR = os.path.join(os.path.dirname(__file__), "data")
WORKSPACE_DIR = os.path.join(os.path.dirname(__file__), "workspace")
FAISS_DATA_DIR = os.path.join(os.path.join(os.path.dirname(__file__), "faiss_data"), "sift")
TRAINING_FILE_PATH = os.path.join(DATA_DIR, "sift_learn.fvecs")

train_filepath = os.path.join(WORKSPACE_DIR, "train.tgz")
train_fvecs_path = os.path.join(FAISS_DATA_DIR, 'sift_learn.fvecs')
train_data = fvecs_read(train_fvecs_path)
with gzip.open(train_filepath, 'wb', compresslevel=1) as f:
    f.write(train_data.tobytes())
