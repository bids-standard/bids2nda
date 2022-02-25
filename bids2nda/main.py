#!/usr/bin/env python
#

# import modules used here -- sys is a very standard one
from __future__ import print_function
import argparse
import csv
import logging
import zipfile
from collections import OrderedDict
from glob import glob
import os
import sys

import nibabel as nb
import json
import pandas as pd
import numpy as np


# Gather our code in a main() function
from shutil import copy


def get_metadata_for_nifti(bids_root, path):

    #TODO support .nii
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


def dict_append(d, key, value):
    if key in d:
        d[key].append(value)
    else:
        d[key] = [value, ]


def cosine_to_orientation(iop):
    """Deduce slicing from cosines

    From http://nipy.org/nibabel/dicom/dicom_orientation.html#dicom-voxel-to
    -patient-coordinate-system-mapping

    From Section C.7.6.1.1.1 we see that the "positive row axis" is left to
    right, and is the direction of the rows, given by the direction of last
    pixel in the first row from the first pixel in that row. Similarly the
    "positive column axis" is top to bottom and is the direction of the columns,
    given by the direction of the last pixel in the first column from the first
    pixel in that column.

    Let's rephrase: the first three values of "Image Orientation Patient" are
    the direction cosine for the "positive row axis". That is, they express the
    direction change in (x, y, z), in the DICOM patient coordinate system
    (DPCS), as you move along the row. That is, as you move from one column to
    the next. That is, as the column array index changes. Similarly, the second
    triplet of values of "Image Orientation Patient" (img_ornt_pat[3:] in
    Python), are the direction cosine for the "positive column axis", and
    express the direction you move, in the DPCS, as you move from row to row,
    and therefore as the row index changes.

    Notes: 
        Modified Yarik's original solution from https://stackoverflow.com/a/45469577 to use the argmax for increaesd flexibility.

    Parameters
    ----------
    iop: list of float
       Values of the ImageOrientationPatient field

    Returns
    -------
    {'Axial', 'Coronal', 'Sagittal'}
    """
    planes = ['Sagittal', 'Coronal', 'Axial']
    plane = np.abs(np.cross(np.round(iop[0:3]), np.round(iop[3:6])))
    return planes[np.argmax(plane)]


def run(args):

    guid_mapping = dict([line.split(" - ") for line in open(args.guid_mapping).read().split("\n") if line != ''])

    suffix_to_scan_type = {"dwi": "MR diffusion",
                           "bold": "fMRI",
                           "sbref": "fMRI",
                           #""MR structural(MPRAGE)",
                           "T1w": "MR structural (T1)",
                           "PD": "MR structural (PD)",
                           #"MR structural(FSPGR)",
                           "T2w": "MR structural (T2)",
                           "FLAIR": "FLAIR",
                           "FLASH": "MR structural (FLASH)",
                           #PET;
                            #ASL;
                            #microscopy;
                            #MR structural(PD, T2);
                            #MR structural(B0 map);
                            #MR structural(B1 map);
                            #single - shell DTI;
                            #multi - shell DTI;
                           "epi": "Field Map",
                           "phase1": "Field Map",
                           "phase2": "Field Map",
                           "phasediff": "Field Map",
                           "magnitude1": "Field Map",
                           "magnitude2": "Field Map",
                           "fieldmap": "Field Map"
                           #X - Ray
                           }

    units_dict = {"mm": "Millimeters",
                  "sec": "Seconds",
                  "msec": "Milliseconds"}

    participants_df = pd.read_csv(os.path.join(args.bids_directory, "participants.tsv"), header=0, sep="\t")

    image03_dict = OrderedDict()
    for file in glob(os.path.join(args.bids_directory, "sub-*", "*", "sub-*.nii.gz")) + \
            glob(os.path.join(args.bids_directory, "sub-*", "ses-*", "*", "sub-*_ses-*.nii.gz")):

        metadata = get_metadata_for_nifti(args.bids_directory, file)

        bids_subject_id = os.path.split(file)[-1].split("_")[0][4:]
        dict_append(image03_dict, 'subjectkey', guid_mapping[bids_subject_id])
        dict_append(image03_dict, 'src_subject_id', bids_subject_id)

        sub = file.split("sub-")[-1].split("_")[0]
        if "ses-" in file:
            ses = file.split("ses-")[-1].split("_")[0]
            scans_file = (os.path.join(args.bids_directory, "sub-" + sub, "ses-" + ses, "sub-" + sub + "_ses-" + ses + "_scans.tsv"))
        else:
            scans_file = (os.path.join(args.bids_directory, "sub-" + sub, "sub-" + sub + "_scans.tsv"))

        if os.path.exists(scans_file):
            scans_df = pd.read_csv(scans_file, header=0, sep="\t")
        else:
            print("%s file not found - information about scan date required by NDA could not be found." % scans_file)
            sys.exit(-1)
        for (_, row) in scans_df.iterrows():
            if file.endswith(row["filename"].replace("/", os.sep)):
                date = row.acq_time
                break

        sdate = date.split("-")
        ndar_date = sdate[1] + "/" + sdate[2].split("T")[0] + "/" + sdate[0]
        dict_append(image03_dict, 'interview_date', ndar_date)

        interview_age = int(round(list(participants_df[participants_df.participant_id == "sub-" + sub].age)[0], 0))*12
        dict_append(image03_dict, 'interview_age', interview_age)

        sex = list(participants_df[participants_df.participant_id == "sub-" + sub].sex)[0]
        dict_append(image03_dict, 'gender', sex)

        dict_append(image03_dict, 'image_file', file)

        suffix = file.split("_")[-1].split(".")[0]
        if suffix == "bold":
            description = suffix + " " + metadata["TaskName"]
            dict_append(image03_dict, 'experiment_id', args.experiment_id)
        else:
            description = suffix
            dict_append(image03_dict, 'experiment_id', args.experiment_id)
        # Shortcut for the global.const section -- apparently might not be flattened fully
        metadata_const = metadata.get('global', {}).get('const', {})
        dict_append(image03_dict, 'image_description', description)
        dict_append(image03_dict, 'scan_type', suffix_to_scan_type[suffix])
        dict_append(image03_dict, 'scan_object', "Live")
        dict_append(image03_dict, 'image_file_format', "NIFTI")
        dict_append(image03_dict, 'image_modality', "MRI")
        dict_append(image03_dict, 'scanner_manufacturer_pd', metadata.get("Manufacturer", ""))
        dict_append(image03_dict, 'scanner_type_pd', metadata.get("ManufacturersModelName", ""))
        dict_append(image03_dict, 'scanner_software_versions_pd', metadata.get("SoftwareVersions", ""))
        dict_append(image03_dict, 'magnetic_field_strength', metadata.get("MagneticFieldStrength", ""))
        dict_append(image03_dict, 'mri_echo_time_pd', metadata.get("EchoTime", ""))
        dict_append(image03_dict, 'flip_angle', metadata.get("FlipAngle", ""))
        dict_append(image03_dict, 'receive_coil', metadata.get("ReceiveCoilName", ""))
        # ImageOrientationPatientDICOM is populated by recent dcm2niix,
        # and ImageOrientationPatient might be provided by exhastive metadata
        # record done by heudiconv
        iop = metadata.get(
            'ImageOrientationPatientDICOM',
            metadata_const.get("ImageOrientationPatient", None)
        )
        dict_append(image03_dict, 'image_orientation', cosine_to_orientation(iop) if iop else '')

        dict_append(image03_dict, 'transformation_performed', 'Yes')
        dict_append(image03_dict, 'transformation_type', 'BIDS2NDA')

        nii = nb.load(file)
        dict_append(image03_dict, 'image_num_dimensions', len(nii.shape))
        dict_append(image03_dict, 'image_extent1', nii.shape[0])
        dict_append(image03_dict, 'image_extent2', nii.shape[1])
        dict_append(image03_dict, 'image_extent3', nii.shape[2])
        if len(nii.shape) > 3:
            image_extent4 = nii.shape[3]
        else:
            image_extent4 = ""

        dict_append(image03_dict, 'image_extent4', image_extent4)
        if suffix == "bold":
            extent4_type = "time"
        elif description == "epi" and len(nii.shape) == 4:
            extent4_type = "time"
        elif suffix == "dwi":
            extent4_type = "diffusion weighting"
        else:
            extent4_type = ""
        dict_append(image03_dict, 'extent4_type', extent4_type)

        dict_append(image03_dict, 'acquisition_matrix', "%g x %g" %(nii.shape[0], nii.shape[1]))

        dict_append(image03_dict, 'image_resolution1', nii.header.get_zooms()[0])
        dict_append(image03_dict, 'image_resolution2', nii.header.get_zooms()[1])
        dict_append(image03_dict, 'image_resolution3', nii.header.get_zooms()[2])
        dict_append(image03_dict, 'image_slice_thickness', metadata_const.get("SliceThickness", nii.header.get_zooms()[2]))
        dict_append(image03_dict, 'photomet_interpret', metadata.get("global",{}).get("const",{}).get("PhotometricInterpretation",""))
        if len(nii.shape) > 3:
            image_resolution4 = nii.header.get_zooms()[3]
        else:
            image_resolution4 = ""
        dict_append(image03_dict, 'image_resolution4', image_resolution4)

        dict_append(image03_dict, 'image_unit1', units_dict[nii.header.get_xyzt_units()[0]])
        dict_append(image03_dict, 'image_unit2', units_dict[nii.header.get_xyzt_units()[0]])
        dict_append(image03_dict, 'image_unit3', units_dict[nii.header.get_xyzt_units()[0]])
        if len(nii.shape) > 3:
            image_unit4 = units_dict[nii.header.get_xyzt_units()[1]]
            if image_unit4 == "Milliseconds":
                TR = nii.header.get_zooms()[3]/1000.
            else:
                TR = nii.header.get_zooms()[3]
            dict_append(image03_dict, 'mri_repetition_time_pd', TR)
        else:
            image_unit4 = ""
            dict_append(image03_dict, 'mri_repetition_time_pd', metadata.get("RepetitionTime", ""))

        dict_append(image03_dict, 'slice_timing', metadata.get("SliceTiming", ""))
        dict_append(image03_dict, 'image_unit4', image_unit4)

        dict_append(image03_dict, 'mri_field_of_view_pd', "%g x %g %s" % (nii.header.get_zooms()[0],
                                                                          nii.header.get_zooms()[1],
                                                                          units_dict[nii.header.get_xyzt_units()[0]]))
        dict_append(image03_dict, 'patient_position', 'head first-supine')

        if file.split(os.sep)[-1].split("_")[1].startswith("ses"):
            visit = file.split(os.sep)[-1].split("_")[1][4:]
        else:
            visit = ""

        dict_append(image03_dict, 'visit', visit)

        if len(metadata) > 0 or suffix in ['bold', 'dwi']:
            _, fname = os.path.split(file)
            zip_name = fname.split(".")[0] + ".metadata.zip"
            with zipfile.ZipFile(os.path.join(args.output_directory, zip_name), 'w', zipfile.ZIP_DEFLATED) as zipf:

                zipf.writestr(fname.replace(".nii.gz", ".json"), json.dumps(metadata, indent=4, sort_keys=True))
                if suffix == "bold":
                    #TODO write a more robust function for finding those files
                    events_file = file.split("_bold")[0] + "_events.tsv"
                    arch_name = os.path.split(events_file)[1]
                    if not os.path.exists(events_file):
                        task_name = file.split("_task-")[1].split("_")[0]
                        events_file = os.path.join(args.bids_directory, "task-" + task_name + "_events.tsv")

                    if os.path.exists(events_file):
                        zipf.write(events_file, arch_name)

            dict_append(image03_dict, 'data_file2', os.path.join(args.output_directory, zip_name))
            dict_append(image03_dict, 'data_file2_type', "ZIP file with additional metadata from Brain Imaging "
                                                                "Data Structure (http://bids.neuroimaging.io)")
        else:
            dict_append(image03_dict, 'data_file2', "")
            dict_append(image03_dict, 'data_file2_type', "")

        if suffix == "dwi":
            # TODO write a more robust function for finding those files
            bvec_file = file.split("_dwi")[0] + "_dwi.bvec"
            if not os.path.exists(bvec_file):
                bvec_file = os.path.join(args.bids_directory, "dwi.bvec")

            if os.path.exists(bvec_file):
                dict_append(image03_dict, 'bvecfile', bvec_file)
            else:
                dict_append(image03_dict, 'bvecfile', "")

            bval_file = file.split("_dwi")[0] + "_dwi.bval"
            if not os.path.exists(bval_file):
                bval_file = os.path.join(args.bids_directory, "dwi.bval")

            if os.path.exists(bval_file):
                dict_append(image03_dict, 'bvalfile', bval_file)
            else:
                dict_append(image03_dict, 'bvalfile', "")
            if os.path.exists(bval_file) or os.path.exists(bvec_file):
                dict_append(image03_dict, 'bvek_bval_files', 'Yes')
            else:
                dict_append(image03_dict, 'bvek_bval_files', 'No')
        else:
            dict_append(image03_dict, 'bvecfile', "")
            dict_append(image03_dict, 'bvalfile', "")
            dict_append(image03_dict, 'bvek_bval_files', "")

        # comply with image03 changes from 12/30/19
        # https://nda.nih.gov/data_structure_history.html?short_name=image03
        
        dict_append(image03_dict, 'deviceserialnumber', "")
        dict_append(image03_dict, 'procdate', "")
        dict_append(image03_dict, 'visnum', "")
        dict_append(image03_dict, 'manifest', "")
        dict_append(image03_dict, 'emission_wavelingth', "")
        dict_append(image03_dict, 'objective_magnification', "")
        dict_append(image03_dict, 'objective_na', "")
        dict_append(image03_dict, 'immersion', "")
        dict_append(image03_dict, 'exposure_time', "")
        dict_append(image03_dict, 'camera_sn', "")
        dict_append(image03_dict, 'block_number', "")
        dict_append(image03_dict, 'level', "")
        dict_append(image03_dict, 'cut_thickness', "")
        dict_append(image03_dict, 'stain', "")
        dict_append(image03_dict, 'stain_details', "")
        dict_append(image03_dict, 'pipeline_stage', "")
        dict_append(image03_dict, 'deconvolved', "")
        dict_append(image03_dict, 'decon_software', "")
        dict_append(image03_dict, 'decon_method', "")
        dict_append(image03_dict, 'psf_type', "")
        dict_append(image03_dict, 'psf_file', "")
        dict_append(image03_dict, 'decon_snr', "")
        dict_append(image03_dict, 'decon_iterations', "")
        dict_append(image03_dict, 'micro_temmplate_name', "")
        dict_append(image03_dict, 'in_stack', "")
        dict_append(image03_dict, 'decon_template_name', "")
        dict_append(image03_dict, 'stack', "")
        dict_append(image03_dict, 'slices', "")
        dict_append(image03_dict, 'slice_number', "")
        dict_append(image03_dict, 'slice_thickness', "")
        dict_append(image03_dict, 'type_of_microscopy', "")

    image03_df = pd.DataFrame(image03_dict)

    with open(os.path.join(args.output_directory, "image03.csv"), "w") as out_fp:
        out_fp.write('"image","3"\n')
        image03_df.to_csv(out_fp, sep=",", index=False, quoting=csv.QUOTE_ALL)

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
        help="Path to a text file with participant_id to GUID mapping. You will need to use the "
             "GUID Tool (https://ndar.nih.gov/contribute.html) to generate GUIDs for your participants.",
        metavar="GUID_MAPPING")
    parser.add_argument(
        "output_directory",
        help="Directory where NDA files will be stored",
        metavar="OUTPUT_DIRECTORY")
    parser.add_argument(
        "experiment_id",
        help="Experiment ID assigned by NDA for collection. Requred for fMRI studies",
        metavar='EXPERIMENT_ID')
    
    args = parser.parse_args()

    run(args)
    print("Metadata extraction complete.")


if __name__ == '__main__':
    main()
