import os
from pathlib import Path
import time

import requests
from dotenv import load_dotenv
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field

project_root = Path(__file__).resolve().parent.parent
load_dotenv(project_root / ".env", override=True)
load_dotenv(project_root / "frontend" / ".env", override=True)

router = APIRouter()


class GenerateRequest(BaseModel):
	document_type: str = Field(min_length=1)
	parties: str = Field(min_length=1)
	terms: str = Field(min_length=1)
	effective_date: str = Field(min_length=1)
	jurisdiction: str = "Not specified"
	additional_instructions: str = ""
	language: str = "English"


def _local_draft(request: GenerateRequest) -> str:
	return f"""{request.document_type}

Effective date: {request.effective_date}
Jurisdiction: {request.jurisdiction}
Language: {request.language}

PARTIES
{request.parties}

AGREEMENT
The parties agree to the following terms, subject to review and completion by the parties and their qualified legal advisers.

TERMS AND CONDITIONS
{request.terms}

ADDITIONAL INSTRUCTIONS
{request.additional_instructions or 'None provided.'}

SIGNATURES

Party 1: ______________________________    Date: ______________

Party 2: ______________________________    Date: ______________

This locally generated draft is a starting point only and is not legal advice. Have it reviewed by a qualified legal professional before use."""


@router.post("/generate")
def generate_document(request: GenerateRequest):
	api_key = os.getenv("GEMINI_API_KEY")
	if not api_key:
		return {
			"content": _local_draft(request),
			"mock_mode": True,
			"model": "Local draft template",
		}

	model = os.getenv("GEMINI_MODEL", "gemini-3.8-flash")
	prompt = f"""Draft a clear {request.document_type} in {request.language}.
This is a draft for review, not legal advice. Do not invent facts; mark missing details as needing completion.
Jurisdiction: {request.jurisdiction}
Effective date: {request.effective_date}
Parties: {request.parties}
Terms: {request.terms}
Additional instructions: {request.additional_instructions or 'None'}"""
	url = f"https://generativelanguage.googleapis.com/v1beta/models/{model}:generateContent"

	try:
		for attempt in range(3):
			try:
				response = requests.post(
					url,
					params={"key": api_key},
					json={"contents": [{"parts": [{"text": prompt}]}]},
					timeout=120,
				)
			except requests.RequestException:
				if attempt == 2:
					raise
				time.sleep(2 ** attempt)
				continue
			if response.status_code != 503 or attempt == 2:
				break
			time.sleep(2 ** attempt)
		response.raise_for_status()
		result = response.json()
		content = result["candidates"][0]["content"]["parts"][0]["text"]
	except requests.HTTPError as error:
		try:
			api_error = error.response.json().get("error", {}).get("message")
		except (ValueError, AttributeError):
			api_error = None
		message = api_error or f"Gemini returned HTTP {error.response.status_code}."
		raise HTTPException(
			status_code=502,
			detail=f"Gemini API error: {message}",
		) from error
	except requests.RequestException as error:
		raise HTTPException(
			status_code=502,
			detail=(
				"Could not connect to the Gemini API after 3 attempts. "
				"Check internet access and allow outbound HTTPS to generativelanguage.googleapis.com."
			),
		) from error
	except (KeyError, IndexError, TypeError, ValueError) as error:
		raise HTTPException(
			status_code=502,
			detail="Gemini returned an unexpected response. Check the configured model and try again.",
		) from error

	return {"content": content, "mock_mode": False, "model": model}
