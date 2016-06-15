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
                        for your participants.
      OUTPUT_DIRECTORY  Directory where NDA files will be stored

    optional arguments:
      -h, --help        show this help message and exit
      

## Example outputs
See [/examples](/examples)
