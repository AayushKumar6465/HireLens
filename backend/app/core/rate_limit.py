"""
Rate limiting setup via slowapi (wraps limits library).

Stricter limits applied to /auth/login and /resumes/upload as per security spec.
"""

from slowapi import Limiter
from slowapi.util import get_remote_address

limiter = Limiter(key_func=get_remote_address)
