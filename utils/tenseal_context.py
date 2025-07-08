import tenseal as ts
import os
import base64
from dotenv import load_dotenv

load_dotenv()
CONTEXT_DIR = os.getenv("CONTEXT_DIR", "context")
os.makedirs(CONTEXT_DIR, exist_ok=True)
PUBLIC_PATH = os.path.join(CONTEXT_DIR, "public.txt")

def read_data(file_name):
    with open(file_name, "rb") as f:
        data = f.read()
    return base64.b64decode(data)

def load_public_context():
    return ts.context_from(read_data(PUBLIC_PATH))