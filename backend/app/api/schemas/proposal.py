from pydantic import BaseModel


class ProposalAnalysisRead(BaseModel):
    message: str
    characters_extracted: int
    preview: str
