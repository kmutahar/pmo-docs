"""Test package setup: disable bytecode so importing shipped scripts leaves no __pycache__."""
import sys

sys.dont_write_bytecode = True
