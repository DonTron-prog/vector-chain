"""PDF text extraction with hybrid approach: pymupdf + VLM fallback."""

import os
import base64
import asyncio
from io import BytesIO
from typing import Optional, List
import fitz  # pymupdf
from pdf2image import convert_from_path
from PIL import Image
import aiohttp
from pydantic_ai import Agent
from pydantic_ai.models.openai import OpenAIModel


class PDFExtractor:
    """Hybrid PDF extractor using pymupdf + VLM fallback."""
    
    def __init__(self, api_key: Optional[str] = None, base_url: Optional[str] = None):
        """Initialize with OpenAI API configuration."""
        self.api_key = api_key or os.getenv("OPENROUTER_API_KEY") or os.getenv("OPENAI_API_KEY")
        self.base_url = base_url or "https://openrouter.ai/api/v1"
        
        # Configure VLM model for fallback
        if self.api_key:
            self.vlm_model = OpenAIModel(
                "openai/gpt-4o-mini",
                api_key=self.api_key,
                base_url=self.base_url
            )
            self.vlm_agent = Agent(
                model=self.vlm_model,
                system_prompt=(
                    "You are an expert at extracting text from financial documents. "
                    "Extract ALL visible text from the image, preserving structure and formatting. "
                    "Focus on financial data, tables, and key information. "
                    "Return only the extracted text, no commentary."
                )
            )
        else:
            self.vlm_model = None
            self.vlm_agent = None
    
    def extract_text_pymupdf(self, pdf_path: str) -> tuple[str, float]:
        """Extract text using pymupdf and assess quality."""
        try:
            doc = fitz.open(pdf_path)
            text = ""
            total_chars = 0
            readable_chars = 0
            
            for page_num in range(len(doc)):
                page = doc[page_num]
                page_text = page.get_text()
                text += f"\n--- Page {page_num + 1} ---\n{page_text}"
                
                # Assess text quality
                total_chars += len(page_text)
                readable_chars += sum(1 for c in page_text if c.isalnum() or c.isspace())
            
            doc.close()
            
            # Calculate quality score (0-1)
            quality_score = readable_chars / max(total_chars, 1) if total_chars > 0 else 0
            
            return text.strip(), quality_score
            
        except Exception as e:
            print(f"pymupdf extraction failed: {e}")
            return "", 0.0
    
    def pdf_to_images(self, pdf_path: str, max_pages: int = 10) -> List[Image.Image]:
        """Convert PDF pages to images for VLM processing."""
        try:
            # Convert PDF to images (limit pages for cost control)
            images = convert_from_path(pdf_path, first_page=1, last_page=max_pages)
            return images
        except Exception as e:
            print(f"PDF to image conversion failed: {e}")
            return []
    
    def image_to_base64(self, image: Image.Image) -> str:
        """Convert PIL image to base64 string."""
        buffer = BytesIO()
        image.save(buffer, format="PNG")
        return base64.b64encode(buffer.getvalue()).decode()
    
    async def extract_text_vlm(self, pdf_path: str, max_pages: int = 10) -> str:
        """Extract text using VLM (gpt-4o-mini)."""
        if not self.vlm_agent:
            return "VLM not configured - API key missing"
        
        try:
            images = self.pdf_to_images(pdf_path, max_pages)
            if not images:
                return "Failed to convert PDF to images"
            
            full_text = ""
            
            for i, image in enumerate(images, 1):
                try:
                    # Convert image to base64
                    image_b64 = self.image_to_base64(image)
                    
                    # Create message with image
                    prompt = f"Extract all text from this financial document page {i}:"
                    
                    # Use pydantic-ai agent to process image
                    result = await self.vlm_agent.run(
                        prompt,
                        message_history=[{
                            "role": "user",
                            "content": [
                                {"type": "text", "text": prompt},
                                {
                                    "type": "image_url",
                                    "image_url": {"url": f"data:image/png;base64,{image_b64}"}
                                }
                            ]
                        }]
                    )
                    
                    page_text = result.data if hasattr(result, 'data') else str(result)
                    full_text += f"\n--- Page {i} (VLM) ---\n{page_text}\n"
                    
                    # Small delay to avoid rate limits
                    await asyncio.sleep(0.5)
                    
                except Exception as e:
                    print(f"VLM processing failed for page {i}: {e}")
                    full_text += f"\n--- Page {i} (VLM Error) ---\nFailed to extract: {e}\n"
            
            return full_text.strip()
            
        except Exception as e:
            print(f"VLM extraction failed: {e}")
            return f"VLM extraction error: {e}"
    
    async def extract_text_hybrid(self, pdf_path: str, quality_threshold: float = 0.7, max_vlm_pages: int = 5) -> str:
        """
        Hybrid extraction: try pymupdf first, fallback to VLM if quality is poor.
        
        Args:
            pdf_path: Path to PDF file
            quality_threshold: Minimum quality score (0-1) to accept pymupdf result
            max_vlm_pages: Maximum pages to process with VLM (cost control)
        """
        # First attempt: pymupdf
        text, quality = self.extract_text_pymupdf(pdf_path)
        
        if quality >= quality_threshold and len(text.strip()) > 100:
            return f"--- Extracted with pymupdf (quality: {quality:.2f}) ---\n{text}"
        
        # Fallback: VLM extraction
        print(f"pymupdf quality too low ({quality:.2f}), falling back to VLM...")
        vlm_text = await self.extract_text_vlm(pdf_path, max_vlm_pages)
        
        # Combine results if pymupdf had some content
        if len(text.strip()) > 50:
            return f"--- Combined extraction (pymupdf + VLM) ---\n{text}\n\n{vlm_text}"
        else:
            return vlm_text


# Convenience functions for streamlit integration
async def extract_pdf_text(pdf_path: str, use_vlm_fallback: bool = True) -> str:
    """Extract text from PDF with hybrid approach."""
    extractor = PDFExtractor()
    
    if use_vlm_fallback:
        return await extractor.extract_text_hybrid(pdf_path)
    else:
        text, _ = extractor.extract_text_pymupdf(pdf_path)
        return text


def extract_pdf_text_sync(pdf_path: str, use_vlm_fallback: bool = True, quality_threshold: float = 0.7) -> str:
    """Synchronous PDF text extraction with optional VLM fallback."""
    extractor = PDFExtractor()
    
    # First try pymupdf
    text, quality = extractor.extract_text_pymupdf(pdf_path)
    
    if quality >= quality_threshold and len(text.strip()) > 100:
        return f"--- Extracted with pymupdf (quality: {quality:.2f}) ---\n{text}"
    
    # If VLM fallback is disabled or no API key, return pymupdf result
    if not use_vlm_fallback or not extractor.api_key:
        return f"--- Extracted with pymupdf only (quality: {quality:.2f}) ---\n{text}"
    
    # VLM fallback (run in new event loop)
    print(f"pymupdf quality too low ({quality:.2f}), falling back to VLM...")
    
    try:
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        vlm_text = loop.run_until_complete(extractor.extract_text_vlm(pdf_path, max_pages=5))
        
        # Combine results if pymupdf had some content
        if len(text.strip()) > 50:
            return f"--- Combined extraction (pymupdf + VLM) ---\n{text}\n\n{vlm_text}"
        else:
            return vlm_text
    finally:
        loop.close()