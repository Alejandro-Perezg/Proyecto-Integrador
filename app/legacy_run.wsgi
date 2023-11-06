import sys
import logging

logging.basicConfig(stream=sys.stderr)
sys.path.insert(0, '/var/www/Proyecto-Integrador/app/')
sys.path.insert(0, '/var/www/Proyecto-Integrador/app/env/lib/python3.10/site-packages')
from main import app as application