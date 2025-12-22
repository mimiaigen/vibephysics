from vibephysics import mapping
import sys

# We use a dummy path since we just want to see if it crashes on import/start
try:
    mapping.glomap_pipeline('/Users/shamangary/codeDemo/data/da3/output/20251220_201123')
except Exception as e:
    print(f"Caught exception: {e}")
except SystemExit as e:
    print(f"System exit: {e}")
