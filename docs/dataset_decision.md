# Dataset Selection Record — PAD-UFES-20

**Decision:** PAD-UFES-20 is the current classification dataset because it contains smartphone-captured clinical skin images, which better match the DermAI mobile-image goal than a dermoscopy-only dataset.

**Status:** selected and analyzed locally; local archive and manifest checksums are recorded below. Dataset source/licence citation still need owner verification before this record is considered complete.

## Local preparation evidence

The recorded audit in `datasets/dataset_audit_report.txt` reports 2,298 source metadata rows, 24 conflicting-diagnosis images excluded, 3 redundant exact copies excluded, and 2,271 eligible images from 1,371 patients. The patient-grouped manifest has 1,592 training, 335 validation, and 344 test images. The report records no patient leakage and no missing/unreadable images in its final integrity check.

Local verification on 2026-10-31: the dataset test module passed **4 tests**. The reproducible [`M1 dataset leakage report`](M1_DATASET_LEAKAGE_REPORT.md) found all 2,271 manifest image files, zero patient and candidate composite-key split overlap, and zero exact image-hash overlap. It also found 116 bare `lesion_id` values across splits/multiple patients and a mismatch between locally counted `(patient_id, lesion_id)` pairs and the paper's stated lesion total. The paper defines `img_id` as composed from patient ID, lesion ID and a random number, which supports (but does not prove) interpreting a lesion key as patient-scoped. The dataset provider's published metadata check does not settle uniqueness scope. Do not call the split lesion-leakage-free until the provider clarifies the identifier semantics and count difference.

- Local archive SHA-256 (`datasets/zr7vgbcyr2-1.zip`): `E8C7E17BAC1698C97E44D4096EC20AC1B91C135285C1446B7B2E7EBBC9BE933C`.
- Local split manifest SHA-256 (`datasets/split_manifest.csv`): `461765564225E796AD1299E74A0A32E2119FDC578F9CBFEF68C84734ADFF970C`.
- These hashes identify local files only; the archive's official source/version and license have not been independently verified.

| Code | Class | Train | Validation | Test | Total |
|---|---|---:|---:|---:|---:|
| ACK | Actinic keratosis | 499 | 107 | 117 | 723 |
| BCC | Basal cell carcinoma | 608 | 123 | 103 | 834 |
| MEL | Melanoma | 30 | 9 | 13 | 52 |
| NEV | Melanocytic nevus | 164 | 40 | 39 | 243 |
| SCC | Squamous cell carcinoma | 127 | 28 | 30 | 185 |
| SEK | Seborrheic keratosis | 164 | 28 | 42 | 234 |

## Limitations and open checks

- MEL is very under-represented (52 images total); metrics for this class will be unstable.
- Resolve the identifier scope and count discrepancy with a provider data dictionary or written clarification. Do not alter the frozen manifest before that resolution.
- Confirm source URL, academic-use licence, citation, download version, archive hash, and whether redistribution is allowed. Do not distribute the dataset archive from this repository.
- The classification manifest contains PAD-UFES-20. The repository also contains ISIC Task 1 image/mask assets; they are a separate source and do not automatically provide masks aligned to PAD images.
- Do not treat dataset results as clinical validation or evidence of performance on arbitrary mobile images.
- There is no healthy-skin class, severity label, or confirmed segmentation mask mapping in the current PAD classification pipeline.
