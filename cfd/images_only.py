"""Export the standard images for the case loaded in the Fluent window. Usage: python images_only.py <tag> [ambient °C]"""
import sys
from fl import connect
from run_case import images

images(connect(), sys.argv[1], float(sys.argv[2]) if len(sys.argv) > 2 else 45.0)
