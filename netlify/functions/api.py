import sys
import os

# Ahora app.py está solo dos niveles arriba, no tres.
sys.path.insert(
    0, 
    os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', '..')
)

from serverless_wsgi import handle_request
import app as flask_module # Esto buscará app.py en la raíz

def handler(event, context):
    return handle_request(flask_module.app, event, context, binary_support=True)