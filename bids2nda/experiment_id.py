"""
NDA requires fMRI tasks have an Experiment ID.
The simplest way to deal with this is
populating the "ExperimentID" key in a _bold.json sidecar.

But at the time of upload,
it many be desirable to leave underlying dataset unmodified.
This provides an alternative:
match input filename against a set of patterns to set the ExperimentID.

Patterns are imported from a tab separated text file.
An EID can have many patterns (why? maybe for extra modalities?)
"""

import re

import pandas as pd

ExperimentID = str


def read_experiment_lookup(tsv_fname: str) -> pd.DataFrame:
    """
    Read in TSV with columns 'ExperimentID' and 'Pattern'. Compile all patterns
    """
    df = pd.read_csv(tsv_fname, sep="\t", header=0)
    if "ExperimentID" not in df.columns or "Pattern" not in df.columns:
        raise ValueError(
            f"Experiment ID pattern tsv lookup file '{tsv_fname}'"
            + "must have columns 'ExperimentID' and 'Pattern'"
        )
    df["ExperimentID"] = [str(x) for x in df.ExperimentID]
    df["Pattern"] = [re.compile(x) for x in df.Pattern]
    return df


def eid_of_filename(eid_lookup, filename: str) -> ExperimentID:
    """
    Try all patterns against filename to find a ExperimentID
    """
    for _, row in eid_lookup.iterrows():
        if row.Pattern.search(filename):
            return row.ExperimentID
    return ""
