"""
Tests for matching Experiment ID to filenames
"""

import os
import os.path
import sys
from io import StringIO
from unittest.mock import patch

import pandas as pd
import pytest
from nibabel.testing import data_path as nibabel_data

import bids2nda.main
from bids2nda.experiment_id import eid_of_filename, read_experiment_lookup


def test_ied_read_bad(tmpdir):
    """errors with bad column"""
    mockfile = StringIO("BadCol\tPattern\n123\ttask-rest\n")
    with pytest.raises(ValueError, match="must have columns"):
        read_experiment_lookup(mockfile)


def test_ied_read():
    """can read and use"""
    mockfile = StringIO("ExperimentID\tPattern\n123\ttask-rest\n")
    df = read_experiment_lookup(mockfile)
    assert eid_of_filename(df, "sub-X/sub-X_task-rest_bold.nii.gz") == "123"
    assert eid_of_filename(df, "sub-X_task-notrest_bold.nii.gz") == ""


def test_full(tmpdir):
    """
    example run
    """
    # build example input -- TODO: create and use files in examples/
    bids = tmpdir.join("in/sub-1/func/")
    os.makedirs(bids)
    os.symlink(
        os.path.join(nibabel_data, "standard.nii.gz"),
        bids.join("sub-1_task-rest_bold.nii.gz"),
    )
    with open(bids.join("sub-1_task-rest_bold.json"), "w") as f:
        f.write('{"TaskName": "rest"}')

    os.symlink(
        os.path.join(nibabel_data, "standard.nii.gz"),
        bids.join("sub-1_task-notrest_bold.nii.gz"),
    )
    with open(bids.join("sub-1_task-notrest_bold.json"), "w") as f:
        f.write('{"TaskName": "notrest"}')

    # age, gender, interview_age
    with open(tmpdir.join("in/participants.tsv"), "w") as f:
        f.write("participant_id\tsex\tage\nsub-1\tM\t100\n")
    with open(tmpdir.join("in/sub-1/sub-1_scans.tsv"), "w") as f:
        f.write(
            "filename\tacq_time\n"
            + "func/sub-1_task-rest_bold.nii.gz\t2020-12-31\n"
            + "func/sub-1_task-notrest_bold.nii.gz\t2020-12-31\n"
        )

    guidmap = tmpdir.join("guidmap.txt")
    with open(guidmap, "w") as f:
        f.write("1 - NDARXXXX")

    exptsv = str(tmpdir.join("expids.tsv"))
    with open(exptsv, "w") as f:
        f.write("ExperimentID\tPattern\n123\ttask-rest\n")

    # run
    sysargs = [
        "bids2nda",
        str(tmpdir.join("in")),
        str(guidmap),
        str(tmpdir.join("out")),
        "--experimentid_tsv",
        exptsv,
    ]
    with patch.object(sys, "argv", sysargs):
        bids2nda.main.main()

    # check output
    # expect task-rest to have exp id 123
    df = pd.read_csv(tmpdir.join("out/image03.txt"), skiprows=1, sep="\t")
    example_with_eid = str(bids.join("sub-1_task-rest_bold.nii.gz"))
    eid = df.experiment_id[df.image_file == example_with_eid].tolist()[0]
    assert eid == 123

    # "notrest" has no match. should be NaN (empty string)
    example_without_eid = str(bids.join("sub-1_task-notrest_bold.nii.gz"))
    eid = df.experiment_id[df.image_file == example_without_eid].tolist()[0]
    assert pd.isna(eid)
