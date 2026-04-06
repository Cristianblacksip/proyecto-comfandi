import sys
import os

# Añadir el directorio de la app Flask al path de Python
sys.path.insert(
    0,
    os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', '..', 'proyecto_comfandi')
)

from serverless_wsgi import handle_request
import app as flask_module


def handler(event, context):
    return handle_request(flask_module.app, event, context, binary_support=True)
