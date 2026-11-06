# M05 pilot

The pilot is an objective geometry test for the narrowed novelty candidate. It
does not use human ratings and it does not claim aesthetic or experiential
quality.

Run tests:

```bash
python -m unittest -v test_core.py
```

Run the preregistered small pilot:

```bash
python run_pilot.py --output outputs --base-seeds 3 --severity 1 --budget 320
```

The primary gate is stored in `outputs/pilot_summary.json`. A pass authorizes a
larger benchmark; it is not paper-level evidence by itself.
