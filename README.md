# BIDS2NDA
Extract [NIMH Data Archive](https://nda.nih.gov/) compatible metadata from [Brain Imaging Data Structure (BIDS)](https://bids-specification.readthedocs.io/) compatible datasets.

This builds a [`image03.csv`](https://nda.nih.gov/data-structure/image03) data structure for upload with [nda-tools](https://github.com/NDAR/nda-tools) or [web uploader](https://nda.nih.gov/vt/).
Data must first be organized in BIDS (see [bids-validator](https://bids-validator.readthedocs.io/en/stable/)) and [NDA's Global Unique IDentifiers](https://nda.nih.gov/nda/data-standards#guid) must have already been generated.

## Installation


    pip install https://github.com/INCF/BIDS2NDA/archive/master.zip


## Usage
<!-- python3 -m bids2nda.main -h -->

    usage: bids2nda [-h] [--experimentid_tsv EXPERIMENTID_TSV] BIDS_DIRECTORY GUID_MAPPING OUTPUT_DIRECTORY

    BIDS to NDA converter.

    positional arguments:
      BIDS_DIRECTORY    Location of the root of your BIDS compatible directory.
      GUID_MAPPING      Path to a text file with participant_id to GUID mapping.
                        You will need to use the GUID Tool
                        (https://ndar.nih.gov/contribute.html) to generate GUIDs
                        for your participants.
      OUTPUT_DIRECTORY  Directory where NDA files will be stored.

    optional arguments:
      -h, --help        Show this help message and exit.
      --experimentid_tsv EXPERIMENTID_TSV
                        Path to TSV file w/cols ExperimentID and Pattern for NDA EID lookup

## Prerequisites

Here is an example directory tree. In addition to BIDS organized `.nii.gz` and `.json` files, you will also need a GUID mapping, participants, and scans file.
```
guid_map.txt # ** GUID_MAPPING file: id lookup
eid_patt.txt # ** optional experiment ID pattern lookup file (vs json sidecar value)
BIDS/
├── participants.tsv # ** Participants File: age, sex
└── sub-10000
    └── ses-1
        ├── anat
        │   ├── sub-10000_ses-1_T1w.json
        │   ├── sub-10000_ses-1_T1w.nii.gz
        ├── func
        │   ├── sub-10000_ses-1_task-rest_bold.json
        │   ├── sub-10000_ses-1_task-rest_bold.nii.gz
        └── sub-10000_ses-1_scans.tsv # ** Scans File: acq_time->interview_date
```


### GUID_MAPPING file format
The is the file format produced by the [GUID Tool](https://nda.nih.gov/nda/nda-tools#guid-tool), one line per subject in the format:

`<participant_id> - <GUID>`

It is not part of the BIDS specification.
The file translates BIDS subject id into NDA participant id (GUID) and can be stored anywhere.
Its location is explicitly given to the `bids2nda` command.

### Participants File
A [Participants File](https://bids-specification.readthedocs.io/en/stable/modality-agnostic-files.html#participants-file) is at the BIDS root like `BIDS/participants.tsv`.
It should at least have columns `participant_id`, `age`, and `sex`.

|col|desc|notes|
|---|---|---|
|`particiapnt_id` | like `sub-X` | does not include session label (See [Sessions File](https://bids-specification.readthedocs.io/en/stable/modality-agnostic-files.html#sessions-file). Not supported here) |
|`age` | number in years | converted to months for NDA's `interview_age`|
|`sex` |||

Contents could look like
```
participant_id	sex	age
sub-100000  	M	46
```

### Scans File

[Scans File](https://bids-specification.readthedocs.io/en/stable/modality-agnostic-files.html#scans-file) is at the session (or subject if session is omitted) level like `BIDS/sub-X/ses-1/sub-X_ses-1_scans.tsv`. 
It must have at least `filename` and `acq_time`.

|col|desc|notes|
|---|---|---|
|`filename`| like `func/sub-X_bold.nii.gz` | relative to session root |
|`acq_time`| date like `YYYY-MM-DD` | creates `interview_date` NDA column|


Contents could look like
```
acq_time	filename
2000-12-31	anat/sub-100000_ses-1_T1w.nii.gz
2000-12-31	func/sub-100000_ses-1_task-rest_bold.nii.gz
```

### ExperimentID
NDA uploads `image03` uploads require the `'experiment_id'` column for fMRI (`_bold.nii.gz`) files.
Experiment IDs are created manually within a collection's experiment tab. See the NDA website's [collection page](https://ndar.nih.gov/user/dashboard/collections.html) and ["create nda experiments" chapter](https://nda.nih.gov/nda/tutorials/nda-experiments?chapter=create-nda-experiments).

#### Sidecar
For `_bold` suffixes, the value stored in the json sidecar with the key `ExperimentID` will be used. That is, `sub-1_task-rest_bold.json` might look like
```
{
 ...
 "ExperimentID": "1234",
}
```

#### ExperimentID Pattern TSV
If you do not want to modify existing sidecars, you can specify IDs based on file name patterns using a dedicated file.

```
bids2nda ... --experimentid_tsv eid_patt.txt
```

where `eid_patt.txt` might look like

```
ExperimentID    Pattern
1234    task-rest
```

## Example outputs
See [/examples](/examples)
