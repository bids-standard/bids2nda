#!/usr/bin/env python
#

# import modules used here -- sys is a very standard one
from __future__ import print_function
import argparse
import csv
import logging
from collections import OrderedDict
from glob import glob
import os
import sys

import nibabel
import json
import pandas as pd


# Gather our code in a main() function
from shutil import copy


def get_metadata_for_nifti(bids_root, path):

    sidecarJSON = path.replace(".nii.gz", ".json")

    pathComponents = os.path.split(sidecarJSON)
    filenameComponents = pathComponents[-1].split("_")
    sessionLevelComponentList = []
    subjectLevelComponentList = []
    topLevelComponentList = []
    ses = None;
    sub = None;

    for filenameComponent in filenameComponents:
        if filenameComponent[:3] != "run":
            sessionLevelComponentList.append(filenameComponent)
            if filenameComponent[:3] == "ses":
                ses = filenameComponent
            else:
                subjectLevelComponentList.append(filenameComponent)
                if filenameComponent[:3] == "sub":
                    sub = filenameComponent
                else:
                    topLevelComponentList.append(filenameComponent)

    topLevelJSON = os.path.join(bids_root, "_".join(topLevelComponentList))
    potentialJSONs = [topLevelJSON]

    subjectLevelJSON = os.path.join(bids_root, sub, "_".join(subjectLevelComponentList))
    potentialJSONs.append(subjectLevelJSON)

    if ses:
        sessionLevelJSON = os.path.join(bids_root, sub, ses, "_".join(sessionLevelComponentList))
        potentialJSONs.append(sessionLevelJSON)

    potentialJSONs.append(sidecarJSON)

    merged_param_dict = {}
    for json_file_path in potentialJSONs:
        if os.path.exists(json_file_path):
            param_dict = json.load(open(json_file_path, "r"))
            merged_param_dict.update(param_dict)

    return merged_param_dict


def run(args):

    guid_mapping = pd.read_csv(args.guid_mapping, sep="\t", header=0,
                               dtype={"participant_id": str})

    image03_df = pd.DataFrame()

    bids_subject_ids = []
    for file in glob(os.path.join(args.bids_directory, "sub-*", "*", "sub-*.nii.gz")) + \
            glob(os.path.join(args.bids_directory, "sub-*", "ses-*", "*", "sub-*_ses-*.nii.gz")):
        bids_subject_id = os.path.split(file)[-1].split("_")[0][4:]
        bids_subject_ids.append(bids_subject_id)

    image03_df['src_subject_id'] = bids_subject_ids
    image03_df = pd.merge(how="left", left=image03_df, left_on="src_subject_id", right=guid_mapping,
                          right_on="participant_id")

    image03_df.drop('participant_id', axis=1, inplace=True)
    image03_df.rename(columns={'GUID': 'subjectkey'}, inplace=True)
    print(image03_df)

    image03_df.to_csv(os.path.join(args.output_directory, "image03.txt"), sep="\t", index=False, quoting=csv.QUOTE_ALL)

def main():
    class MyParser(argparse.ArgumentParser):
        def error(self, message):
            sys.stderr.write('error: %s\n' % message)
            self.print_help()
            sys.exit(2)

    parser = MyParser(
        description="BIDS to NDA converter.",
        fromfile_prefix_chars='@')
    # TODO Specify your real parameters here.
    parser.add_argument(
        "bids_directory",
        help="Location of the root of your BIDS compatible directory",
        metavar="BIDS_DIRECTORY")
    parser.add_argument(
        "guid_mapping",
        help="Path to a Tab Separated Value (TSV) file with participant_id to GUID mapping. You will need to use the "
             "GUID Tool (https://ndar.nih.gov/contribute.html) to generate GUIDs for your participants.",
        metavar="GUID_MAPPING")
    parser.add_argument(
        "output_directory",
        help="Directory where NDA files will be stored",
        metavar="OUTPUT_DIRECTORY")
    args = parser.parse_args()

    run(args)
    print("Metadata extraction complete.")


if __name__ == '__main__':
    main()
