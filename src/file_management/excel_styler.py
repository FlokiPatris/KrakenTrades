from __future__ import annotations

# =============================================================================
# 📦 Imports
# =============================================================================
from pathlib import Path
from typing import Iterable, List

from openpyxl import Workbook, load_workbook
from openpyxl.cell.cell import Cell
from openpyxl.styles import PatternFill
from openpyxl.utils import get_column_letter
from openpyxl.worksheet.worksheet import Worksheet

from kraken_core import ExcelStyling, custom_logger


# =============================================================================
# 🛠 Helper Functions
# =============================================================================
def _auto_adjust_columns(ws: Worksheet) -> None:
    """Auto-adjust column widths with a max width limit from ExcelStyling."""
    for col in ws.columns:
        max_width: int = max(len(str(cell.value) or "") for cell in col) + 4

        col_index: int | None = col[0].column
        if col_index is None:
            continue

        col_letter: str = get_column_letter(col_index)
        ws.column_dimensions[col_letter].width = min(
            max_width, ExcelStyling.MAX_COLUMN_WIDTH
        )


def _style_header(ws: Worksheet) -> None:
    """Apply bold + center alignment to header row."""
    for cell in ws[ExcelStyling.HEADER_ROW_INDEX]:
        cell.font = ExcelStyling.BOLD_FONT
        cell.alignment = ExcelStyling.CENTER_ALIGNMENT


def _style_portfolio_sheet(ws: Worksheet) -> None:
    """Apply Portfolio-specific formatting."""
    custom_logger.info("📊 Styling Portfolio sheet")
    for row in ws.iter_rows(min_row=2):
        row[0].alignment = ExcelStyling.LEFT_ALIGNMENT
        row[1].alignment = ExcelStyling.RIGHT_ALIGNMENT

        if str(row[0].value) == "Result":
            row[1].font = ExcelStyling.BOLD_FONT
            row[1].fill = (
                ExcelStyling.GREEN_FILL
                if "up" in str(row[1].value).lower()
                else ExcelStyling.RED_FILL
            )


def _insert_roi_section(
    ws: Worksheet,
    title: str,
    fill: PatternFill,
    row_list: List[Iterable[Cell]],
    start_row: int,
) -> None:
    """Insert a titled section with conditional coloring into the Asset ROI sheet."""
    custom_logger.info(f"📌 Inserting section: {title}")
    last_col = ws.max_column
    ws.insert_rows(start_row)
    ws.merge_cells(
        start_row=start_row,
        start_column=1,
        end_row=start_row,
        end_column=last_col,
    )

    title_cell = ws.cell(row=start_row, column=1)
    title_cell.value = title
    title_cell.font = ExcelStyling.BOLD_FONT
    title_cell.alignment = ExcelStyling.CENTER_ALIGNMENT
    title_cell.fill = fill

    for i, row in enumerate(row_list, start=start_row + 1):
        for j, cell in enumerate(row, start=1):
            new_cell = ws.cell(row=i, column=j, value=cell.value)
            if j in (12, 13) and isinstance(cell.value, (int, float)):
                new_cell.fill = (
                    ExcelStyling.GREEN_FILL
                    if cell.value >= 0
                    else ExcelStyling.RED_FILL
                )


def _style_asset_roi_sheet(ws: Worksheet, group_by: str = "roi") -> None:
    """
    Generic Asset ROI sheet styling and grouping.

    group_by options:
        - "roi" → Positive vs Negative ROI
        - "remaining_volume" → Unsold vs Sold assets based on Remaining Volume
    """
    custom_logger.info(f"📈 Styling Asset ROI sheet (group_by={group_by})")

    headers = [cell.value for cell in ws[1]]
    rows = list(ws.iter_rows(min_row=2, max_row=ws.max_row))

    # --- Determine grouping column ---
    if group_by == "roi":
        try:
            col_idx = headers.index("ROI (%)")
        except ValueError:
            custom_logger.error("❌ ROI (%) column not found in Asset ROI sheet")
            return
        pos_rows = [
            r for r in rows if r[col_idx].value is not None and r[col_idx].value >= 0
        ]
        neg_rows = [
            r for r in rows if r[col_idx].value is not None and r[col_idx].value < 0
        ]

        ws.delete_rows(2, ws.max_row)

        if pos_rows:
            _insert_roi_section(
                ws, "🟢 Positive ROI Assets 🟢", ExcelStyling.GREEN_FILL, pos_rows, 2
            )
        if neg_rows:
            _insert_roi_section(
                ws,
                "🔻 Negative ROI Assets 🔻",
                ExcelStyling.RED_FILL,
                neg_rows,
                3 + len(pos_rows),
            )

    elif group_by == "remaining_volume":
        try:
            col_idx = headers.index("Remaining Volume")
        except ValueError:
            custom_logger.error(
                "❌ Remaining Volume column not found in Asset ROI sheet"
            )
            return
        unsold_rows = [r for r in rows if r[col_idx].value and r[col_idx].value > 0]
        sold_rows = [
            r for r in rows if r[col_idx].value is not None and r[col_idx].value <= 0
        ]

        ws.delete_rows(2, ws.max_row)

        if unsold_rows:
            _insert_roi_section(
                ws,
                "📦 Unsold Assets (Still Holding)",
                ExcelStyling.GREEN_FILL,
                unsold_rows,
                2,
            )
        if sold_rows:
            _insert_roi_section(
                ws,
                "💰 Sold Assets (Closed Positions)",
                ExcelStyling.RED_FILL,
                sold_rows,
                3 + len(unsold_rows),
            )

    else:
        custom_logger.warning(
            f"⚠️ Unknown group_by value '{group_by}', skipping grouping."
        )


def _style_token_sheet(ws: Worksheet) -> None:
    """Apply token-specific formatting for alignment consistency."""
    custom_logger.info(f"📄 Styling token sheet: {ws.title}")

    col_names: List[str] = [cell.value for cell in ws[ExcelStyling.HEADER_ROW_INDEX]]

    for row in ws.iter_rows(min_row=2):
        for col_idx, cell in enumerate(row, start=1):
            col_name: str = (
                col_names[col_idx - 1] if col_idx - 1 < len(col_names) else ""
            )
            cell.alignment = (
                ExcelStyling.LEFT_ALIGNMENT
                if col_name in ExcelStyling.LEFT_ALIGNED_COLUMNS
                else ExcelStyling.RIGHT_ALIGNMENT
            )


def _reorder_sheets(wb: Workbook) -> None:
    """Reorder sheets so Portfolio comes first, Asset ROI second, then tokens."""
    custom_logger.info("🔀 Reordering sheets")
    wb._sheets.sort(
        key=lambda s: (
            0
            if s.title == ExcelStyling.PORTFOLIO_SHEET
            else 1 if s.title == ExcelStyling.ASSET_ROI_SHEET else 2
        )
    )


# =============================================================================
# 🎨 Core Function
# =============================================================================
def style_excel(output: Path) -> None:
    """
    Apply styling to the Excel workbook at the given path.
    Includes formatting for Portfolio, Asset ROI, and individual token sheets.
    """
    custom_logger.info(f"📄 Loading workbook: {output}")
    wb = load_workbook(output)

    # --- General formatting ---
    for sheet_name in wb.sheetnames:
        ws = wb[sheet_name]
        custom_logger.info(f"🎨 Formatting sheet: {sheet_name}")
        _auto_adjust_columns(ws)
        _style_header(ws)

    # --- Portfolio sheet ---
    if ExcelStyling.PORTFOLIO_SHEET in wb.sheetnames:
        _style_portfolio_sheet(wb[ExcelStyling.PORTFOLIO_SHEET])

    # --- Asset ROI sheet ---
    if ExcelStyling.ASSET_ROI_SHEET in wb.sheetnames:
        _style_asset_roi_sheet(wb[ExcelStyling.ASSET_ROI_SHEET])

    # --- Token sheets ---
    for sheet_name in wb.sheetnames:
        if sheet_name not in {
            ExcelStyling.PORTFOLIO_SHEET,
            ExcelStyling.ASSET_ROI_SHEET,
        }:
            _style_token_sheet(wb[sheet_name])

    # --- Reorder & Save ---
    _reorder_sheets(wb)
    wb.save(output)
    custom_logger.info(f"✅ Workbook saved: {output}")
