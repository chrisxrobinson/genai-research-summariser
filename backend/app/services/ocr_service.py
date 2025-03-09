import base64
import tempfile
from typing import Dict, Optional

from mistralai import Mistral

from ..config import get_settings

settings = get_settings()


class OCRService:
    def __init__(self):
        self.client = Mistral(api_key=settings.mistral_api_key)

    async def process_pdf(self, pdf_content: bytes) -> Optional[str]:
        """
        Process PDF using Mistral OCR API
        Args:
            pdf_content: Binary PDF content
        Returns:
            Extracted text as string or None if processing failed
        """
        try:
            # Create a temporary file for the PDF
            with tempfile.NamedTemporaryFile(
                suffix=".pdf", delete=False
            ) as temp_pdf:
                temp_pdf.write(pdf_content)
                temp_pdf_path = temp_pdf.name
            # Convert PDF to base64
            with open(temp_pdf_path, "rb") as pdf_file:
                pdf_base64 = base64.b64encode(pdf_file.read()).decode("utf-8")
            # Process with Mistral OCR
            ocr_response = self.client.ocr.process(
                model="mistral-ocr-latest",
                document={
                    "type": "document_base64",
                    "document_base64": pdf_base64,
                },
                include_image_base64=False,
            )
            # Extract text from response
            extracted_text = ""
            for page in ocr_response.pages:
                for block in page.blocks:
                    extracted_text += block.text + "\n"
            return extracted_text.strip()
        except Exception as e:
            print(f"PDF processing error: {e}")
            return None

    async def extract_metadata(self, text: str) -> Dict:
        """
        Extract metadata from the OCR text using Mistral AI
        Args:
            text: OCRed text from PDF
        Returns:
            Dictionary with extracted metadata
        """
        try:
            # Use Mistral to extract metadata from text
            prompt = f"""
            Extract the following information from this research paper text:
            - Title
            - Authors (as a list)
            - Publication date (YYYY-MM-DD format if available)
            - Abstract summary (first 200 words)
            - Keywords or topics
            Return the information in JSON format with these exact keys:
            "title", "authors", "publication_date", "abstract", "keywords"
            Here is the text:
            {text[:2000]}  # Using first 2000 chars as that's usually enough for metadata
            """
            response = self.client.chat(
                model="mistral-large-latest",
                messages=[{"role": "user", "content": prompt}],
            )
            extracted_text = response.choices[0].message.content
            # Parse the JSON response
            import json
            import re

            # Find JSON block in the response
            json_match = re.search(
                r"```json\n(.*?)\n```", extracted_text, re.DOTALL
            )
            if json_match:
                json_str = json_match.group(1)
            else:
                json_str = extracted_text
            # Clean up any non-JSON content
            json_str = re.sub(r"^[^{\[]+", "", json_str)
            json_str = re.sub(r"[^}\]]+$", "", json_str)
            metadata = json.loads(json_str)
            # Ensure required fields exist
            metadata.setdefault("title", "Untitled Document")
            metadata.setdefault("authors", [])
            metadata.setdefault("publication_date", None)
            metadata.setdefault("abstract", "")
            metadata.setdefault("keywords", [])
            return metadata
        except Exception as e:
            print(f"Metadata extraction error: {e}")
            return {
                "title": "Untitled Document",
                "authors": [],
                "publication_date": None,
                "abstract": "",
                "keywords": [],
            }


# Initialize OCR service singleton
ocr_service = OCRService()
