import os
import re
import pandas as pd
import sys
import torch
import json
import argparse

import numpy as np
import time

from pathlib import Path
from sklearn.metrics.cluster import normalized_mutual_info_score
from tslearn.clustering import TimeSeriesKMeans, KShape
from utils.metrics import consistency, purity
from utils.preprocessing import load_data_kshape


def random_seed(seed):
    torch.manual_seed(seed)
    if torch.cuda.is_available():
        torch.cuda.manual_seed_all(args.seed)
    np.random.seed(args.seed)


def parse_arguments():
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--data_dir",
        type=str,
        required=True,
        help="dir holding sequences as separate files",
    )
    parser.add_argument("--num_clusters", type=int, required=True, help="number of clusters")
    parser.add_argument("--num_events", type=int, required=True, help="number of events")
    args = parser.parse_args()
    return args


sys.path.append("..")


if __name__ == "__main__":

    args = parse_arguments()
    info_score = np.zeros((args.num_clusters + 1, args.num_clusters + 1))

    # loading data
    Ts_reshaped = load_data_kshape(args.data_dir, args.num_events)
    # ground truth labels
    gt = pd.read_csv(Path(args.data_dir, "clusters.csv"))["cluster_id"].to_numpy()
    gt_ids = torch.LongTensor(gt)

    tested_models = ["k_shape", "k_means_softdtw"]

    for modelname in tested_models:
        time_start = time.time()
        if modelname == "k_shape":
            model = KShape(n_clusters=args.num_clusters, max_iter=10)
        elif modelname == "k_means_softdtw":
            model = TimeSeriesKMeans(n_clusters=args.num_clusters, metric="softdtw", max_iter=10)

        labels = model.fit_predict(Ts_reshaped)
        labels = torch.LongTensor(labels)
        time_overall = time.time() - time_start

        if gt_ids is not None:
            purity_value = purity(labels, gt_ids)
            print(f"Purity {modelname}: {purity_value:.4f}")
            print(f"Run time {modelname}: {time_overall}")
            metrics = {
                "Purity": f"{purity_value:.4f}",
                "Run time": f"{time_overall:.4f}",
                # "Normalized mutual info score:": f"{info_score}",
                # "Predictive log likelihood:":f'{log_loss(gt_ids, labels):.4f}',
                "Predicted labels": f"{labels}",
            }
            # I wouldn't put labels into metrics file
            with open(Path(args.data_dir, "metrics.json"), "w") as f:
                json.dump(metrics, f, indent=4)
        else:
            pass
            # this part is not implemented anywhere
            # metrics = {
            #    "Run time": f"{time_mean:.4f}+-{time_std:.4f}",
            #    "Predictive log likelihood:": f"{nll_mean.item():.4f}+-{nll_std.item():.4f}",
            #    "Predicted labels": f"{labels}",
            # }
            # with open(Path(args.data_dir, args.save_to), "w") as f:
            #       json.dump(metrics, f, indent=4)
