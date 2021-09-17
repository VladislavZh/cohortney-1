"""
This file contains implementation of metrics from A Dirichlet Mixture Model 
of Hawkes Processes for Event Sequence Clustering
https://arxiv.org/pdf/1701.09177.pdf
"""
import torch
import numpy as np

from sklearn.metrics.cluster import normalized_mutual_info_score


def consistency(trials_labels):
    """
    Args:
    - trials_labels - array-like sequence of 1-D tensors. Each tensor is a sequence of labels
    """
    J = len(trials_labels)
    values = torch.zeros(J)

    for trial_id, labels in enumerate(trials_labels):
        ks = torch.unique(labels)
        sz_M = 0  # number of pairs within same cluster
        for k in ks:
            mask = labels == k
            sz = mask.sum()
            s = sz * (sz - 1.0) / 2.0
            sz_M += s

        for trial_id2, labels2 in enumerate(trials_labels):
            if trial_id == trial_id2:
                continue

            for k in ks:
                mask = labels == k
                s2 = 0
                for k2 in labels2[mask].unique():
                    sz = (
                        labels2[mask] == k2
                    ).sum()  # same cluster within j trial, same cluster within j' trial
                    s2 += sz * (sz - 1.0) / 2.0
                # values[trial_id] += (sz_M - s2) / ((J-1) * sz_M)
                values[trial_id] += s2
        values[trial_id] /= (J - 1) * sz_M

    return torch.min(values)


def purity(learned_ids, gt_ids):
    """
    Args:
    - learned_ids - 1-D tensor of labels obtained from model
    - gt_ids - 1-D tensor of ground truth labels
    """
    assert len(learned_ids) == len(gt_ids)
    pur = 0
    ks = torch.unique(learned_ids)
    js = torch.unique(gt_ids)
    for k in ks:
        inters = []
        for j in js:
            inters.append(((learned_ids == k) * (gt_ids == j)).sum().item())
        pur += 1.0 / len(learned_ids) * max(inters)

    return pur


def update_info_score(info_score, learned_labels, gt_labels, K, nruns):
    """
    Information score
    """
    for i in range(1, K + 1):
        info_score[i, 0] = i - 1
        for j in range(1, K + 1):
            info_score[0, j] = j - 1
            ind = np.concatenate(
                [np.argwhere(gt_labels == j - 1), np.argwhere(gt_labels == i - 1)],
                axis=1,
            )[0]
            a = learned_labels.tolist()
            b = gt_labels.tolist()
            info_score[i, j] += (
                normalized_mutual_info_score([b[k] for k in ind], [a[k] for k in ind])
                / nruns
            )
    return info_score