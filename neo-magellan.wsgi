#!/user/bin/python3
import sys

if sys.version_info[0]<3:       # require python3
    raise Exception("Python3 required! Current (wrong) version: '%s'" % sys.version_info)

sys.path.insert(0, '/var/www/NeoMagellan/')
from main import app as application
application.secret_key = 'A0Zr98j/3yX R~XHH!jmN]LWX/,?RThow'
