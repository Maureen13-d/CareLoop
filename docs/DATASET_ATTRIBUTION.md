# Dataset attribution

## Citation

Maina E., Wanzare L., Obuhuma J., Ayere M., Kang'ahi M., Okutoyi J. "Kenyan sign language word-based pose dataset." *Data in Brief* 60:111502 (2025). doi:10.1016/j.dib.2025.111502

Data: Zenodo, doi:10.5281/zenodo.14974973

- Paper: https://doi.org/10.1016/j.dib.2025.111502
- Data: https://doi.org/10.5281/zenodo.14974973

## What it is

An open dataset of Kenyan Sign Language words recorded as body pose landmarks, published by researchers at Maseno University. The files are anonymized pose data. They are single signed words, not sentences and not messages to a patient.

## How CareLoop uses it

CareLoop may download the files into `data/external/ksl_pose/` with `scripts/fetch_ksl_dataset.py`. That folder is gitignored. The download stays off until a person reads the Zenodo licence and sets `ksl_dataset.license_verified` to true in `config/ksl_dataset.yaml`. Checksums from the Zenodo record are required before a file is kept.

The words are research samples. They are not patient messages, they are not reviewed clinical lines, and they must not be served by `/ksl/clip`, a conversation template, the patient card, or Telegram.

This repository does not contain the dataset. The licence checklist in `docs/DATASET_LICENSE_CHECK.md` is blank until a person fills it. Faces and identities must not be reconstructed from the landmarks, and the pose data must not be combined with other data to re-identify signers.
