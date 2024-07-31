from __future__ import absolute_import

import os
import sys
from pathlib import Path

BASE_DIR = Path(__file__).resolve(strict=True).parent.parent.parent
sys.path.append(str(BASE_DIR / "core"))

env_path = os.path.join(BASE_DIR, ".env")

if not os.path.exists(env_path):
    sys.exit("create `.env file`")