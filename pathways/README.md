# Pathways

A care pathway is **configuration, not code**: stages, owners, deadlines, who may move a case, and closure rules. The backend reads these files at start-up (`backend/app/modules/pathways/loader.py`).

To add a pathway, copy `cervical_cancer.yaml`, change the states, and ask the backend to load it by its `id`.

Rules:
- Every deadline must be either sourced (add a comment with the source) or marked **ASSUMED**.
- Do not describe a pathway as clinically validated. It is a demo definition.
