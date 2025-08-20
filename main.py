from src.file_management import (
    build_trade_dataframe,
    extract_kraken_trade_records_from_pdf,
    style_excel,
    write_excel,
)
from src.kraken_core import FileLocations


def main() -> None:
    extracted_pdf_records = extract_kraken_trade_records_from_pdf(
        FileLocations.KRAKEN_TRADES_PDF
    )
    formatted_data_frames = build_trade_dataframe(extracted_pdf_records)

    write_excel(formatted_data_frames, FileLocations.PARSED_TRADES_EXCEL)
    style_excel(FileLocations.PARSED_TRADES_EXCEL)


if __name__ == "__main__":
    main()
