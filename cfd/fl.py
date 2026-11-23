"""Connect to the Fluent solver window started with -sifile=server_info.txt (see start_fluent.ps1)."""
import os
import ansys.fluent.core as pf

HERE = os.path.dirname(os.path.abspath(__file__))
SIFILE = os.path.join(HERE, "server_info.txt")


def connect():
    return pf.connect_to_fluent(server_info_file_name=SIFILE, cleanup_on_exit=False)
