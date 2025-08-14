# bandit_trigger.py
import subprocess
import hashlib

# Insecure: shell=True
subprocess.call("ls -l", shell=True)  # nosec

# Weak hash
hashlib.md5(b"test").hexdigest()

# Dangerous eval
eval("2 + 2")


AWS_SECRET_ACCESS_KEY = "AKIA1234567890ABCDEF"
API_KEY = "1234567890abcdef"
SYS_ADMIN_PASSWORD = "SuperSecretPasswordY123"
