# KSL vocabulary report

Labels were matched to file names in the open zip `10.5281/zenodo.14338329`. A match is the gloss text only. It is not a claim that the sign means the CareLoop menu item. A Deaf reviewer has to decide that.

The archive does not name signers. The counts below are distinct recording-folder ids. See `docs/KSL_DATASET_INSPECTION.md` for how those folders are laid out. There are 728 distinct glosses and 1,495 landmark files across 40 folders.

## Menu concepts

| CareLoop word | Exact gloss | Files | Recording folders | Similar names that were not used |
|---|---|---|---|---|
| yes | not found | 0 | 0 | YESTERDAY |
| no | NO | 3 | 148, 173, 65 | |
| same | SAME | 5 | 112, 201, 233, 251, 264 | |
| better | BETTER | 1 | 196 | |
| worse | not found | 0 | 0 | |
| help | HELP | 6 | 167, 174, 201, 205, 208, 65 | |
| clinic | not found | 0 | 0 | |
| hospital | HOSPITAL | 1 | 91 | |
| go | GO | 12 | 103, 129, 131, 148, 154, 162, 173, 201, 206, 208, 233, 65 | |
| pain | PAIN | 3 | 205, 232, 233 | |
| money | MONEY | 2 | 238, 65 | |
| transport | TRANSPORT | 1 | 201 | |
| afraid | not found | 0 | 0 | |
| interpreter | not found | 0 | 0 | INTERPRET |
| repeat | not found | 0 | 0 | |
| stop | STOP | 3 | 251, 264, 91 | |

`INTERPRET` is not `INTERPRETER`. `YESTERDAY` is not `yes`. Neither was counted as a match.

Every exact match still needs a Deaf reviewer. `GO` is especially easy to misread: the English gloss does not say whether the sign is the menu's "go".

## Hands in the first opened file

The normalizer in R04 has not scored these clips. This is not a quality ranking. It is what the opcode walk saw in one file per gloss. Pose and face were present on every frame of these files. Hands were often missing.

| Gloss | Frames in that file | Frames missing a hand |
|---|---|---|
| NO | 16 | left hand missing on all 16 |
| SAME | 20 | left 3, right 13 |
| BETTER | 35 | right 9 |
| HELP | 21 | left 7, right 11 |
| HOSPITAL | 30 | left 23 |
| GO | 20 | right 13 |
| PAIN | 38 | left 3, right 2 |
| MONEY | 40 | left 40, right 19 |
| TRANSPORT | 61 | left 21, right 21 |
| STOP | 36 | left 30 |

## Provisional shortlist

Seven glosses occur in more than one recording folder: `GO`, `HELP`, `SAME`, `NO`, `STOP`, `PAIN`, and `MONEY`. That is the shortlist for a later demo pass. It is not a list of clean clips. `BETTER`, `HOSPITAL`, and `TRANSPORT` exist, and each has only one folder.

`YES`, `WORSE`, `CLINIC`, `AFRAID`, `INTERPRETER`, and `REPEAT` are not in this public file under those names. A research demo cannot show those words from this zip without inventing a match.
