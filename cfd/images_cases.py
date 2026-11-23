"""Read each saved case+data into the Fluent window and export the standard images. Usage: python images_cases.py tag1 tag2 ..."""
import os, sys
from fl import connect, HERE
from run_case import images

s = connect()
for tag in sys.argv[1:]:
    s.settings.file.read_case_data(file_name=os.path.join(HERE, f"hotend_{tag}.cas.h5"))
    images(s, tag)
