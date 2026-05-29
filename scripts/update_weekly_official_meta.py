#!/usr/bin/env python3
from __future__ import annotations

import json
import os
from datetime import datetime, timedelta, timezone
from typing import Any, Dict, List, Optional, Tuple

import requests
from supabase import create_client
from tenacity import retry, retry_if_exception_type, stop_after_attempt, wait_exponential

TAIPEI_TZ = timezone(timedelta(hours=8))
TODAY_TPE = datetime