#!"C:\Users\riooms\OneDrive - Deloitte (O365D)\Thesis\development\AutoML_v1\env\Scripts\python.exe"
# EASY-INSTALL-ENTRY-SCRIPT: 'rq==1.0','console_scripts','rq'
__requires__ = 'rq==1.0'
import re
import sys
from pkg_resources import load_entry_point

if __name__ == '__main__':
    sys.argv[0] = re.sub(r'(-script\.pyw?|\.exe)?$', '', sys.argv[0])
    sys.exit(
        load_entry_point('rq==1.0', 'console_scripts', 'rq')()
    )
