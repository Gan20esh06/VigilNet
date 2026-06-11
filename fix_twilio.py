import subprocess
import sys

print("=== Checking current Twilio version ===")
try:
    import twilio
    print(f"Current twilio version: {twilio.__version__}")
except Exception as e:
    print(f"Error importing twilio: {e}")

print("\n=== Upgrading Twilio ===")
result = subprocess.run(
    [sys.executable, "-m", "pip", "install", "--upgrade", "twilio"],
    capture_output=True, text=True
)
print(result.stdout)
if result.stderr:
    print("STDERR:", result.stderr)

print("\n=== Checking new Twilio version ===")
# Force reimport
import importlib
if 'twilio' in sys.modules:
    del sys.modules['twilio']

result2 = subprocess.run(
    [sys.executable, "-c", "import twilio; print(twilio.__version__)"],
    capture_output=True, text=True
)
print(f"New twilio version: {result2.stdout.strip()}")

print("\n=== Testing Twilio Client import ===")
result3 = subprocess.run(
    [sys.executable, "-c", "from twilio.rest import Client; print('Client import OK')"],
    capture_output=True, text=True
)
print(result3.stdout.strip())
if result3.stderr:
    print("Error:", result3.stderr)
