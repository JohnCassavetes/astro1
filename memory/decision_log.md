# Decision Log

**2026-03-09 20:37** - Repository Initialized
- Decision: Create structured repo at ~/Desktop/astro1
- Rationale: Need single source of truth for reproducible project
- Files created: README, .gitignore, requirements.txt, memory/*.json

**2026-03-09 20:40** - Pipeline Architecture Set
- Decision: 7-stage pipeline (download → preprocess → embed → detect → filter → review → figures)
- Rationale: Modular, debuggable, allows checkpointing
- Each stage writes to results/ and updates memory/

**2026-03-09 20:50** - Repository Setup Complete
- Decision: All scripts and documentation created
- Files created:
  - 7 pipeline scripts (download → figures)
  - Paper draft (draft.md)
  - Documentation (README, methodology, runbook, project plan)
  - Memory tracking files (8 JSON files)
- Status: Ready for data collection phase

**Pending Decisions:**
- [x] Which embedding method? → ResNet50 ImageNet (fastest, proven)
- [x] Which anomaly detector? → IsolationForest (fast, interpretable)
- [x] Sample size target? → 10k (weekend-feasible)
- [x] Cutout size? → 30 arcsec (standard)
