# BIDS2NDA
Extract NIHM Data Archive compatible metadata from Brain Imaging Data Structure compatible datasets

## Installation


    pip install https://github.com/INCF/BIDS2NDA/archive/master.zip


## Usage

    usage: bids2nda [-h] [-v] BIDS_DIRECTORY GUID_MAPPING OUTPUT_DIRECTORY

    BIDS to NDA converter.

    positional arguments:
      BIDS_DIRECTORY    Location of the root of your BIDS compatible directory
      GUID_MAPPING      Path to a text file with participant_id to GUID mapping.
                        You will need to use the GUID Tool
                        (https://ndar.nih.gov/contribute.html) to generate GUIDs
                        for your participants. Formatted as  <participant_id> - <GUID>
      OUTPUT_DIRECTORY  Directory where NDA files will be stored
      EXPERIMENT_ID     experiment_id value assigned from NDA after setting the study up throught the NDA website (int)

    optional arguments:
      -h, --help        show this help message and exit


## GUID_MAPPING file format
The is the file format produced by the GUID Tool: one line per subject in the format:

`<participant_id> - <GUID>`

If your ids are in the format of `sub-sid001420`, be sure to not include 'sub-' in your `<participant_id>` e.g., `<sid001420> - <GUID>`

## Example outputs
See [/examples](/examples)

## Notes:
Column experiment_id must be manually filled in for now.
This is based on experiment ID's received from NDA after setting the study up through the NDA website [here](https://ndar.nih.gov/user/dashboard/collections.html).
