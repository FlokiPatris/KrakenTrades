# =======================================================
# 🧩 Imports
# =======================================================
import os
import json
from pathlib import Path
from pydrive2.auth import GoogleAuth
from pydrive2.drive import GoogleDrive
from oauth2client.service_account import ServiceAccountCredentials
from kraken_core import PathsConfig, custom_logger


# =======================================================
# 🔑 Credentials Loading
# =======================================================
def load_service_account_creds(env_var: str) -> dict:
    """Load JSON credentials from environment variable."""
    try:
        creds_json = json.loads(os.environ[env_var])
        return creds_json
    except KeyError:
        custom_logger.error(f"Environment variable '{env_var}' is not defined.")
        raise
    except json.JSONDecodeError as e:
        custom_logger.error(f"Invalid JSON in '{env_var}': {e}")
        raise


# =======================================================
# 🔗 Google Drive Setup
# =======================================================
def setup_drive(creds_json: dict) -> GoogleDrive:
    """Authenticate with Google Drive using service account."""
    try:
        gauth = GoogleAuth()
        scope = "https://www.googleapis.com/auth/drive"
        credentials = ServiceAccountCredentials.from_json_keyfile_dict(
            creds_json, scope
        )
        gauth.credentials = credentials
        drive = GoogleDrive(gauth)
        return drive
    except ValueError as e:
        custom_logger.error(f"Failed to create Google Drive credentials: {e}")
        raise
    except Exception as e:
        custom_logger.error(f"Unexpected error during Google Drive setup: {e}")
        raise


# =======================================================
# 📄 File Download Logic
# =======================================================
def download_file(drive: GoogleDrive, file_id: str, output_path: Path) -> None:
    """Download file from Google Drive to output_path."""
    try:
        file = drive.CreateFile({"id": file_id})
        file.GetContentFile(str(output_path))
        custom_logger.info(f"✅ File from Google Drive downloaded to: {output_path}")
    except FileNotFoundError as e:
        custom_logger.error(f"Output path not found: {output_path} — {e}")
        raise
    except PermissionError as e:
        custom_logger.error(f"No permission to write to {output_path} — {e}")
        raise
    except Exception as e:
        custom_logger.error(f"Failed to download file {file_id} to {output_path}: {e}")
        raise


# =======================================================
# 🏁 Main Execution
# =======================================================
def main() -> None:
    # Load credentials
    creds_json = load_service_account_creds("GOOGLE_DRIVE_JSON_KEY")

    # Authenticate with Google Drive
    drive = setup_drive(creds_json)

    # Download the target file
    file_id = "1qWAkAYZTY3oZK-eK41F4Psuhdm4cAUub"
    download_file(drive, file_id, PathsConfig.KRAKEN_TRADES_PDF)


# =======================================================
# 🔧 Entry Point
# =======================================================
if __name__ == "__main__":
    main()
