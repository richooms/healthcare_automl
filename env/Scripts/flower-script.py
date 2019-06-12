#!"C:\Users\riooms\OneDrive - Deloitte (O365D)\Thesis\development\AutoML_v1\env\Scripts\python.exe"
# EASY-INSTALL-ENTRY-SCRIPT: 'flower==0.9.3','console_scripts','flower'
__requires__ = 'flower==0.9.3'
import re
import sys
from pkg_resources import load_entry_point

if __name__ == '__main__':
    sys.argv[0] = re.sub(r'(-script\.pyw?|\.exe)?$', '', sys.argv[0])
    sys.exit(
        load_entry_point('flower==0.9.3', 'console_scripts', 'flower')()
    )
