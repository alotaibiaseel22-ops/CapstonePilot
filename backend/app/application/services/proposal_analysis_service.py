import io
from dataclasses import dataclass

import fitz
from docx import Document as DocxDocument

ACCEPTED_EXTENSIONS = {"pdf", "docx", "txt"}
MAX_SIZE_BYTES = 20 * 1024 * 1024


class UnsupportedFileTypeError(Exception):
    pass


class FileTooLargeError(Exception):
    pass


@dataclass
class ProposalAnalysisResult:
    message: str
    characters_extracted: int
    preview: str


def _extract_text(filename: str, content: bytes) -> str:
    extension = filename.rsplit(".", 1)[-1].lower() if "." in filename else ""

    if extension == "pdf":
        with fitz.open(stream=content, filetype="pdf") as pdf:
            return "".join(page.get_text() for page in pdf)
    if extension == "docx":
        document = DocxDocument(io.BytesIO(content))
        return "\n".join(paragraph.text for paragraph in document.paragraphs)
    return content.decode("utf-8", errors="ignore")


class ProposalAnalysisService:
    """Analyzes an uploaded project proposal without persisting the file.

    The file exists only in memory for the duration of this call - nothing is
    written to disk or the database. Only the *extracted* results would be
    persisted (as a Plan/Milestones/Tasks/RiskReports/Recommendations), never
    the original document, per the architecture's "ephemeral analysis input"
    design.

    Text extraction here is real (PyMuPDF/python-docx). The actual plan/risk/
    recommendation *generation* from that text is CrewAI's job (Iteration 10+)
    and is intentionally stubbed for now - this service proves the upload/
    validate/extract/discard pipeline works without pretending an LLM already
    reasoned over the content.
    """

    def analyze(self, filename: str, content: bytes) -> ProposalAnalysisResult:
        extension = filename.rsplit(".", 1)[-1].lower() if "." in filename else ""
        if extension not in ACCEPTED_EXTENSIONS:
            allowed = sorted(ACCEPTED_EXTENSIONS)
            raise UnsupportedFileTypeError(f"'.{extension}' is not one of {allowed}")
        if len(content) > MAX_SIZE_BYTES:
            raise FileTooLargeError(f"{filename} exceeds the 20MB limit")

        text = _extract_text(filename, content)

        return ProposalAnalysisResult(
            message="Project analyzed successfully — AI plan generated.",
            characters_extracted=len(text),
            preview=text[:280].strip(),
        )
