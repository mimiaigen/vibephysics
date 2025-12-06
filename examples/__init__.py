"""
Examples for vibephysics.

This module provides a helper to import vibephysics modules
that works both with pip-installed package and local development.
"""

import sys
import os

def setup_imports():
    """
    Setup import paths to work both with:
    - pip install vibephysics (installed package)
    - Local development (running from repo)
    
    Call this at the start of example scripts:
        from examples import setup_imports
        setup_imports()
        
        from vibephysics.foundation import scene, physics
        from vibephysics.annotation import AnnotationManager
    """
    # First, try if vibephysics is already installed
    try:
        import vibephysics
        return  # Already available, nothing to do
    except ImportError:
        pass
    
    # Not installed, add src/ to path for local development
    repo_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
    src_path = os.path.join(repo_root, 'src')
    
    if src_path not in sys.path:
        sys.path.insert(0, src_path)
    
    # Verify it works now
    try:
        import vibephysics
    except ImportError:
        raise ImportError(
            "Could not import vibephysics. Either:\n"
            "  1. pip install vibephysics\n"
            "  2. pip install -e . (from repo root)\n"
            "  3. Run from the repo root directory"
        )
