import asyncio
import logging
import os
import sys
import time

from google import genai
from google.genai import types
from tenacity import retry, stop_after_attempt, wait_exponential

from app.core.config import settings
from app.core.prompts import PDF_ACADEMIC_OCR_PROMPT, PDF_HANDWRITING_PROMPT
from app.utils.split_pdf import split_pdf

logger = logging.getLogger(__name__)

DEFAULT_PDF_MODEL_ID = settings.PDF_GEMINI_MODEL
DEFAULT_PDF_CHUNK_SIZE = settings.PDF_CHUNK_SIZE
DEFAULT_PDF_TEMPERATURE = settings.PDF_GEMINI_TEMPERATURE
DEFAULT_PDF_TOP_P = settings.PDF_GEMINI_TOP_P
DEFAULT_PDF_PROCESSING_TIMEOUT_SECONDS = settings.PDF_PROCESSING_TIMEOUT_SECONDS
DEFAULT_PDF_POLL_INTERVAL_SECONDS = settings.PDF_POLL_INTERVAL_SECONDS
DEFAULT_PDF_MAX_CONCURRENCY = settings.PDF_MAX_CONCURRENCY


class PDFExtractionService:
    """Service for extracting text from PDFs using Google Gemini's multimodal capabilities.

    This service handles the full lifecycle of interacting with the Google Generative AI
    Files API, including file upload, polling for processing completion, and generating
    formatted text content using specific prompts.

    Attributes:
        client: The Google GenAI client instance.
        model_id: The default model ID to use for extraction (e.g., "gemini-2.5-flash").
    """

    def __init__(self, api_key: str = settings.GOOGLE_API_KEY):
        """Initializes the PDFExtractionService.

        Args:
            api_key: The Google Cloud/Vertex AI API key. Defaults to settings.GOOGLE_API_KEY.

        Raises:
            ValueError: If the API key is not provided or empty.
        """
        if not api_key:
            error_msg = "GOOGLE_API_KEY is not set. PDF service cannot function."
            logger.error(error_msg)
            raise ValueError(error_msg)

        self.client = genai.Client(api_key=api_key)
        self.model_id = DEFAULT_PDF_MODEL_ID

    # --- Sync helpers for Tenacity Retry ---

    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=4, max=10),
        reraise=True,
    )
    def _upload_file_sync(self, path: str):
        """Uploads a file synchronously with retry logic."""
        return self.client.files.upload(file=path)

    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=4, max=10),
        reraise=True,
    )
    def _poll_file_sync(self, name: str):
        """Polls the file status synchronously with retry logic."""
        return self.client.files.get(name=name)

    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=4, max=10),
        reraise=True,
    )
    def _generate_content_sync(self, model_id: str, contents, config):
        """Generates content synchronously via the model with retry logic."""
        return self.client.models.generate_content(
            model=model_id, contents=contents, config=config
        )

    # --- Main Async Logic ---

    async def _process_pdf_with_gemini(
        self, file_path: str, prompt: str, model_id: str
    ) -> str:
        """Orchestrates the PDF extraction process via Google Gemini.

        This internal method handles the sequence of:
        1. Uploading the PDF to Google AI Studio.
        2. Polling until the file is in an 'ACTIVE' state.
        3. Sending a generation request with the provided prompt.
        4. Cleaning up the uploaded file from the cloud.

        Args:
            file_path: The absolute path to the local PDF file.
            prompt: The text prompt to guide the model's extraction behavior.
            model_id: The specific Gemini model ID to use for generation.

        Returns:
            The extracted text content as a string.

        Raises:
            FileNotFoundError: If the specified file_path does not exist.
            TimeoutError: If file processing takes longer than the allowed timeout.
            Exception: For any API errors during upload, polling, or generation.
        """
        if not os.path.exists(file_path):
            raise FileNotFoundError(f"File not found: {file_path}")

        file_upload = None
        try:
            logger.info(f"Uploading {os.path.basename(file_path)} to AI Studio...")

            # 1. Upload
            file_upload = await asyncio.to_thread(self._upload_file_sync, file_path)

            # 2. Poll with Timeout
            start_time = time.time()
            timeout_seconds = DEFAULT_PDF_PROCESSING_TIMEOUT_SECONDS

            while file_upload.state.name == "PROCESSING":
                elapsed = time.time() - start_time
                if elapsed > timeout_seconds:
                    raise TimeoutError(
                        f"File processing timed out after {timeout_seconds}s"
                    )

                logger.info(f"Processing PDF... ({int(elapsed)}s)")
                await asyncio.sleep(DEFAULT_PDF_POLL_INTERVAL_SECONDS)

                file_upload = await asyncio.to_thread(
                    self._poll_file_sync, file_upload.name
                )

            logger.info(f"File Status: {file_upload.state.name}")

            if file_upload.state.name != "ACTIVE":
                raise Exception(f"File upload failed. State: {file_upload.state.name}")

            # 3. Generate
            logger.info(f"Extracting with {model_id} (Temperature=0)...")

            response = await asyncio.to_thread(
                self._generate_content_sync,
                model_id=model_id,
                contents=[
                    types.Content(
                        role="user",
                        parts=[
                            types.Part.from_uri(
                                file_uri=file_upload.uri,
                                mime_type=file_upload.mime_type,
                            ),
                            types.Part.from_text(text=prompt),
                        ],
                    )
                ],
                config=types.GenerateContentConfig(
                    temperature=DEFAULT_PDF_TEMPERATURE,
                    top_p=DEFAULT_PDF_TOP_P,
                ),
            )

            logger.info("Content extraction successful.")
            return response.text

        except Exception as e:
            logger.error(f"Error extracting PDF: {e}")
            raise e

        finally:
            if file_upload:
                try:
                    logger.info("Cleaning up cloud file...")
                    await asyncio.to_thread(
                        self.client.files.delete, name=file_upload.name
                    )
                    logger.info("Deleted cloud file.")
                except Exception as cleanup_err:
                    logger.warning(f"Cleanup warning: {cleanup_err}")

    async def _extract_text_with_chunking(
        self,
        file_path: str,
        prompt: str,
        model_id: str,
        chunk_size: int = DEFAULT_PDF_CHUNK_SIZE,
        max_concurrency: int = DEFAULT_PDF_MAX_CONCURRENCY,
        chunk_type: str = "chunk",
    ) -> str:
        """Generic method to extract text from a PDF with chunking support.

        This internal method handles the common workflow of splitting a PDF into chunks,
        processing each chunk with Gemini. Temporary files are automatically cleaned up
        by the split_pdf context manager.

        Args:
            file_path: Absolute path to the PDF file.
            prompt: The prompt to use for extraction.
            model_id: The Gemini model ID to use.
            chunk_size: Number of pages per chunk (default: 20).
            max_concurrency: Maximum number of chunks to process concurrently.
            chunk_type: Descriptive name for logging (e.g., "chunk", "handwritten chunk").

        Returns:
            The extracted content as a Markdown-formatted string.

        Raises:
            FileNotFoundError: If the file does not exist.
        """
        concurrency = max(1, max_concurrency)
        cm = split_pdf(file_path, chunk_size)
        chunks = await asyncio.to_thread(cm.__enter__)
        exc_type = exc = tb = None

        try:
            sem = asyncio.Semaphore(concurrency)

            async def process_chunk(i: int, chunk_path: str) -> str:
                async with sem:
                    logger.info(
                        f"Processing {chunk_type} {i + 1}/{len(chunks)}: {chunk_path}"
                    )
                    return await self._process_pdf_with_gemini(
                        chunk_path, prompt=prompt, model_id=model_id
                    )

            tasks = [
                asyncio.create_task(process_chunk(i, chunk_path))
                for i, chunk_path in enumerate(chunks)
            ]
            results = await asyncio.gather(*tasks, return_exceptions=True)
            errors = [result for result in results if isinstance(result, Exception)]
            if errors:
                raise errors[0]

            return "\n\n".join(results)
        except Exception:
            exc_type, exc, tb = sys.exc_info()
            raise
        finally:
            await asyncio.to_thread(cm.__exit__, exc_type, exc, tb)

    async def extract_text_from_formatted_pdf(
        self,
        file_path: str,
        model_id: str | None = None,
        prompt: str | None = None,
        chunk_size: int = DEFAULT_PDF_CHUNK_SIZE,
        max_concurrency: int = DEFAULT_PDF_MAX_CONCURRENCY,
    ) -> str:
        """Extracts text from a structured/academic PDF into Markdown.

        Uses a prompt optimized for academic papers, handling dual columns,
        formulas (converted to LaTeX), and removing references. Automatically
        splits large PDFs into chunks to avoid token limits.

        Args:
            file_path: Absolute path to the PDF file.
            model_id: Optional; overrides valid default model (e.g. 'gemini-2.5-flash').
            prompt: Optional; overrides default academic OCR prompt.
            chunk_size: Number of pages per chunk (default: 20).
            max_concurrency: Maximum number of chunks to process concurrently.

        Returns:
            The extracted content as a Markdown-formatted string.

        Raises:
            FileNotFoundError: If the file does not exist.
            ValueError: If API key configuration is missing.
        """
        target_model_id = model_id or self.model_id
        target_prompt = prompt or PDF_ACADEMIC_OCR_PROMPT.strip()

        return await self._extract_text_with_chunking(
            file_path=file_path,
            prompt=target_prompt,
            model_id=target_model_id,
            chunk_size=chunk_size,
            max_concurrency=max_concurrency,
            chunk_type="chunk",
        )

    async def extract_handwritten_notes(
        self,
        file_path: str,
        model_id: str | None = None,
        chunk_size: int = DEFAULT_PDF_CHUNK_SIZE,
        max_concurrency: int = DEFAULT_PDF_MAX_CONCURRENCY,
    ) -> str:
        """Extracts text from handwritten notes or unstructured documents.

        Uses a prompt optimized for handwriting recognition, handling illegible text,
        diagram descriptions, and non-linear layouts. Supports chunking.

        Args:
            file_path: Absolute path to the PDF file.
            model_id: Model to use (defaults to settings.PDF_GEMINI_MODEL).
            chunk_size: Number of pages per chunk (default: 20).
            max_concurrency: Maximum number of chunks to process concurrently.

        Returns:
            The extracted content as a Markdown-formatted string.

        Raises:
            FileNotFoundError: If the file does not exist.
        """
        target_prompt = PDF_HANDWRITING_PROMPT.strip()

        target_model_id = model_id or self.model_id

        return await self._extract_text_with_chunking(
            file_path=file_path,
            prompt=target_prompt,
            model_id=target_model_id,
            chunk_size=chunk_size,
            max_concurrency=max_concurrency,
            chunk_type="handwritten chunk",
        )

