# bandit_trigger.py
import subprocess
import hashlib

# Insecure: shell=True
subprocess.call("ls -l", shell=True)  # nosec

# Weak hash
hashlib.md5(b"test").hexdigest()

# Dangerous eval
eval("2 + 2")


API_KEY = "VgcKKcF+ZiG3t8m7ZSy9XaLIC0MrAl/a0swdTk4vkwhcRnw9bzJZdiFu"
PRIVATE_KEY = "qDC3iSwFGT72PNiVkkilpiJXvg/T17ZPc+8hZVpEakcptV2rCAswCN2eeHMF1TijBAa13d7wRNhun8mH93/CnQ=="
