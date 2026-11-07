import io

from docx import Document


class DocxBuilder:
    """Writes a real Word document with python-docx — a heading, body paragraphs, a list
    item and a table between them — so the loader is tested against the format Word
    produces, including the order of paragraphs and tables in the body."""

    def build(self, title = None, heading = "Deployment", paragraphs = ("Run the migration first.",),
        table = (("Step", "Owner"), ("Migrate", "Ana")), closing = "Then restart the service."):
        document = Document()
        if title is not None:
            document.core_properties.title = title
        document.add_heading(heading, level = 1)
        for current_paragraph in paragraphs:
            document.add_paragraph(current_paragraph)
        document.add_paragraph("Check the logs.", style = "List Bullet")
        if table:
            grid = document.add_table(rows = len(table), cols = len(table[0]))
            for row_index, current_row in enumerate(table):
                for column_index, current_cell in enumerate(current_row):
                    grid.cell(row_index, column_index).text = current_cell
        document.add_paragraph(closing)

        buffer = io.BytesIO()
        document.save(buffer)
        return buffer.getvalue()
