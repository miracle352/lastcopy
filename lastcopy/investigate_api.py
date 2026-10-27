"""POST /investigate: JSON in, JSON out, bundled examples only (no client paths)."""
import threading
from typing import Literal
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, ConfigDict

router = APIRouter()
_lock = threading.Lock()
NAMES = {'fleet': 'example_1.json', 'spreadsheet': 'example_2.json', 'photo': 'example_3.json', 'stranded': 'example_4.json'}


class InvestigateRequest(BaseModel):
    model_config = ConfigDict(extra='forbid')
    example: Literal['fleet', 'spreadsheet', 'photo', 'stranded'] = 'fleet'


@router.post('/investigate')
def investigate(body: InvestigateRequest):
    from run import ROOT, investigate as run_example
    with _lock:
        try:
            return run_example(ROOT / 'input_examples' / NAMES[body.example], quiet=True)
        except SystemExit as error:
            raise HTTPException(500, {'type': 'InvestigationFailed', 'message': str(error), 'recoverable': True}) from None
