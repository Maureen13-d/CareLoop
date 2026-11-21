# Dataset licence check

Filled from the Zenodo API on 21 Nov 2026, after the project owner confirmed the check in chat. This is not a lawyer's opinion.

- Zenodo record: https://doi.org/10.5281/zenodo.14974973
- Licence name on Zenodo: Creative Commons Attribution 4.0 International (`cc-by-4.0`), on both the cited record and the earlier open version
- Attribution requirements: credit the authors, the dataset title, and the DOI
- Restrictions: the cited record `10.5281/zenodo.14974973` has `access_right: restricted` and the API lists no public files. The earlier version `10.5281/zenodo.14338329` is `access_right: open` under the same licence and is the file CareLoop can actually read. One public file: `Pose Data.zip`, 1,539,828,602 bytes, Zenodo checksum `md5:3cf8e3b30583ea1be34a65d285099b65`
- Date checked: 21 Nov 2026
- Who checked: project owner, confirmed in chat. Record metadata read from the Zenodo API the same day
- Notes: do not reconstruct faces or try to identify the signers. The pose files are pickled object arrays. Do not load them with `allow_pickle` inside the app.

`ksl_dataset.license_verified` is true because of that confirmation. The download script still will not fetch unless it is run with `--download`, and it refuses when the disk cannot hold the archive.
