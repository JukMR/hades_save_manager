# README.md

## Canonical usage

### Semantic checkpoint
python hades_save.py backup --tag em4 --tag sword --note "Reached Styx with 3 DD"

### List with metadata
python hades_save.py list --meta

### Restore last snapshot tagged em4
python hades_save.py restore-tag em4

### Restore exact snapshot
python hades_save.py restore 2026-01-24T18-30-02

