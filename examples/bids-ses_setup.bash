#!/usr/bin/env bash
mkdir -p bids-ses/sub-{a,b}/ses-{1,2}/{func,anat}
for d in bids-ses/sub-{a,b}/ses-{1,2}/func/; do [[ $d =~ sub-./ses-. ]] && touch $d/${BASH_REMATCH/\//_}_task-rest_bold.{nii.gz,json};done
for d in bids-ses/sub-{a,b}/ses-{1,2}/anat/; do [[ $d =~ sub-./ses-. ]] && touch $d/${BASH_REMATCH/\//_}_T1w.{nii.gz,json};done

 find examples/ -iname '*.json'  | while read f; do echo '{}' > $f; done
 find examples/ -iname '*rest*.json'  | while read f; do echo '{"TaskName": "rest"}' > $f; done

 find examples/ -iname '*.nii.gz' | while read f; do echo '0 0 0 0' | 3dUndump -overwrite -prefix $f -dimen 2 2 2 -dval 1 - ; done
