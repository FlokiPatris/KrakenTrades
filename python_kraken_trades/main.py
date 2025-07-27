import os
from constants import FileLocations
from python_kraken_trades.excel.excel_styler import style_excel
from python_kraken_trades.excel.excel_writer import write_excel
from pdf_parser import extract_kraken_trade_records_from_pdf, build_trade_dataframe

def main() -> None:
    extracted_pdf_records = extract_kraken_trade_records_from_pdf(FileLocations.KRAKEN_TRADES_PDF)
    formatted_data_frames = build_trade_dataframe(extracted_pdf_records)

    write_excel(formatted_data_frames, FileLocations.PARSED_TRADES_EXCEL)
    style_excel(FileLocations.PARSED_TRADES_EXCEL)

    # ✅ Auto-open the Excel file (Windows only)
    os.startfile(FileLocations.PARSED_TRADES_EXCEL)

if __name__ == "__main__":
    main()