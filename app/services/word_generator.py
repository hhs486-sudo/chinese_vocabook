import copy
import os
import uuid

from docx import Document
from docx.shared import Pt

TEMPLATE_PATH = os.path.join(os.path.dirname(__file__), "..", "..", "중국어단어장.docx")
TEMP_DIR = os.path.join(os.path.dirname(__file__), "..", "..", "temp")


def _copy_row_style(source_row, target_row):
    """Copy row height and cell styles from source to target row."""
    target_row.height = source_row.height
    for src_cell, tgt_cell in zip(source_row.cells, target_row.cells):
        tgt_cell.width = src_cell.width
        if src_cell.paragraphs and tgt_cell.paragraphs:
            src_para = src_cell.paragraphs[0]
            tgt_para = tgt_cell.paragraphs[0]
            tgt_para.alignment = src_para.alignment
            if src_para.paragraph_format.space_before is not None:
                tgt_para.paragraph_format.space_before = src_para.paragraph_format.space_before
            if src_para.paragraph_format.space_after is not None:
                tgt_para.paragraph_format.space_after = src_para.paragraph_format.space_after


def generate_word(words: list[dict], job_id: str | None = None) -> str:
    """Generate a Word file from extracted words using the template.

    Args:
        words: List of dicts with 'chinese', 'pinyin', 'korean' keys.
        job_id: Optional job ID for the filename.

    Returns:
        Path to the generated Word file.
    """
    doc = Document(os.path.abspath(TEMPLATE_PATH))
    table = doc.tables[0]

    data_start_row = 1  # row 0 is header
    available_rows = len(table.rows) - data_start_row  # 28 rows

    # Add extra rows if needed
    if len(words) > available_rows:
        template_row = table.rows[data_start_row]
        for _ in range(len(words) - available_rows):
            new_row = table.add_row()
            _copy_row_style(template_row, new_row)

    # Fill in data
    for i, word in enumerate(words):
        row = table.rows[data_start_row + i]
        cells = row.cells

        # cells[0] = 한자, cells[3] = 병음, cells[5] = 뜻
        cells[0].paragraphs[0].text = word.get("chinese", "")
        cells[3].paragraphs[0].text = word.get("pinyin", "")
        cells[5].paragraphs[0].text = word.get("korean", "")

    # Save to temp directory
    os.makedirs(TEMP_DIR, exist_ok=True)
    file_id = job_id or str(uuid.uuid4())
    output_path = os.path.join(TEMP_DIR, f"{file_id}.docx")
    doc.save(output_path)

    return output_path
