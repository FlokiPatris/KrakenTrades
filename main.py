from pathlib import Path
from src.file_management import (
    build_trade_dataframe,
    extract_kraken_trade_records_from_pdf,
    style_excel,
    write_excel,
)
from src.kraken_core import FileLocations


def get_output_dir() -> Path:
    """Return the folder to write output files to.

    - In Docker, use /app/uploads
    - Locally, use current working directory
    """
    docker_uploads = Path("/app/uploads")
    if docker_uploads.exists():
        return docker_uploads
    return Path(".")


def main() -> None:
    # Extract PDF records
    extracted_pdf_records = extract_kraken_trade_records_from_pdf(
        FileLocations.KRAKEN_TRADES_PDF
    )

    # Build DataFrame
    formatted_data_frames = build_trade_dataframe(extracted_pdf_records)

    # Determine output path
    output_dir = get_output_dir()
    output_file = (
        output_dir / FileLocations.PARSED_TRADES_EXCEL.name
    )  # keep same filename

    # Write and style Excel
    write_excel(formatted_data_frames, output_file)
    style_excel(output_file)

    print(f"✅ Report written to: {output_file}")


if __name__ == "__main__":
    main()
