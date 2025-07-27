# === main.py ===
from constants import PARSED_TRADES_EXCEL_PATH, KRAKEN_TRADES_PDF_PATH
from python_kraken_trades.excel.excel_styler import style_excel
from python_kraken_trades.excel.excel_writer import write_excel
from pdf_parser import parse_pdf

def main() -> None:
    data_frame = parse_pdf(KRAKEN_TRADES_PDF_PATH)
    write_excel(data_frame, PARSED_TRADES_EXCEL_PATH)
    style_excel(PARSED_TRADES_EXCEL_PATH)

if __name__ == "__main__":
    main()