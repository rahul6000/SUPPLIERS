# Enhanced GPT-4o AI extraction with comprehensive product description extraction
import openai
import json
import os
from typing import Dict, Any, List
import re

# Direct API key for now
OPENAI_API_KEY = os.getenv('OPENAI_API_KEY')

# Initialize OpenAI client (modern API)
client = openai.OpenAI(api_key=OPENAI_API_KEY)

def extract_data_and_supplier(pdf_text: str) -> Dict[str, Any]:
    """Extract comprehensive supplier and product data from PDF text using OpenAI GPT-4o with enhanced product descriptions"""
    
    # Check if API key is configured
    if not OPENAI_API_KEY or OPENAI_API_KEY == "YOUR_OPENAI_API_KEY":
        print("❌ ERROR: No OpenAI API Key configured")
        return _create_error_response("No OpenAI API Key configured")

    # Pre-scan text for currency symbols to help guide AI
    currency_hints = []
    text_upper = pdf_text.upper()
    if '$' in pdf_text:
        currency_hints.append('$')
    if '€' in pdf_text:
        currency_hints.append('€')
    if 'USD' in text_upper:
        currency_hints.append('USD')
    if 'EUR' in text_upper:
        currency_hints.append('EUR')
    if 'CAD' in text_upper:
        currency_hints.append('CAD')
    if 'AUD' in text_upper:
        currency_hints.append('AUD')
    if 'CHF' in text_upper:
        currency_hints.append('CHF')
    
    print(f"[ai_extractor] Currency hints from text scan: {currency_hints}")

    try:
        print(f"🚀 Starting AI extraction with {len(pdf_text)} characters of PDF text")
        prompt = _build_enhanced_prompt(pdf_text, currency_hints)
        print(f"📝 Prompt built, sending to OpenAI...")
        
        response = client.chat.completions.create(
            model="gpt-4o",
            messages=[
                {"role": "system", "content": "You are an expert document analyzer specializing in comprehensive product description extraction. Return detailed, accurate JSON data with complete product information including full descriptions, specifications, and attributes."},
                {"role": "user", "content": prompt}
            ],
            temperature=0.1,
            max_tokens=4000
        )
        
        ai_response = response.choices[0].message.content.strip()
        print(f"🤖 DEBUG - Raw AI Response:")
        print(f"   Response length: {len(ai_response)} chars")
        print(f"   First 500 chars: {ai_response[:500]}")
        
        try:
            extracted_data = _parse_json_response(ai_response)
            print(f"🔍 DEBUG - Parsed JSON keys: {list(extracted_data.keys())}")
            normalized_data = _normalize_extracted_data(extracted_data)
            return normalized_data
            
        except json.JSONDecodeError as e:
            print(f"JSON parsing error: {e}")
            return _create_fallback_response(pdf_text)
            
    except Exception as e:
        print(f"OpenAI API error: {e}")
        return _create_error_response(str(e))
    
    # Check if API key is configured
    if not OPENAI_API_KEY or OPENAI_API_KEY == "YOUR_OPENAI_API_KEY":
        print("[EXTRACT] ERROR: No API key configured")
        return _create_error_response("No OpenAI API Key configured")
    
    print(f"[EXTRACT] API key present: {OPENAI_API_KEY[:10]}...")
    
    try:
        prompt = _build_enhanced_prompt(pdf_text)
        print(f"[EXTRACT] Enhanced prompt built: {len(prompt)} chars")
        
        print("[ai_extractor] Sending enhanced request to OpenAI")
        response = client.chat.completions.create(
            model="gpt-4o",
            messages=[
                {"role": "system", "content": "You are an expert document analyzer specializing in comprehensive product description extraction. Return detailed, accurate JSON data with complete product information including full descriptions, specifications, and attributes."},
                {"role": "user", "content": prompt}
            ],
            temperature=0.1,
            max_tokens=4000  # Increased for fuller descriptions
        )
        
        ai_response = response.choices[0].message.content.strip()
        print("[ai_extractor] Raw AI response received")
        print("[DEBUG] First 1000 chars of AI response:", ai_response[:1000])
        print("[DEBUG] Looking for currency field in AI response...")
        if '"currency"' in ai_response:
            # Find the currency field value
            start = ai_response.find('"currency"')
            snippet = ai_response[max(0, start-50):start+150]
            print(f"[DEBUG] Currency field context: {snippet}")
        else:
            print("[DEBUG] No currency field found in AI response!")
        
        try:
            extracted_data = _parse_json_response(ai_response)
            print("[DEBUG] Parsed data keys:", list(extracted_data.keys()))
            print("[DEBUG] Currency field:", extracted_data.get('currency'))
            print("[DEBUG] Supplier name field:", extracted_data.get('supplier_name'))
            print("[DEBUG] Supplier object:", extracted_data.get('supplier'))
            if 'products' in extracted_data:
                print("[DEBUG] Number of products:", len(extracted_data['products']))
                if extracted_data['products']:
                    first_product = extracted_data['products'][0]
                    print("[DEBUG] First product keys:", list(first_product.keys()))
                    print("[DEBUG] First product currency:", first_product.get('currency'))
                    print("[DEBUG] First product price:", first_product.get('price'))
                    print("[DEBUG] First product original_price:", first_product.get('original_price'))
            
            normalized_data = _normalize_extracted_data(extracted_data)
            
            # CRITICAL FIX: If AI didn't extract currency, add it manually
            if not normalized_data.get('currency') or normalized_data.get('currency') == '£':
                if currency_hints:
                    # Use the first detected currency hint
                    fallback_currency = currency_hints[0]
                    normalized_data['currency'] = fallback_currency
                    print(f"[ai_extractor] CURRENCY FALLBACK: AI didn't extract currency, using detected: {fallback_currency}")
                    
                    # Also update product currencies
                    for product in normalized_data.get('products', []):
                        if not product.get('currency') or product.get('currency') == '£':
                            product['currency'] = fallback_currency
            
            print(f"[ai_extractor] Successfully extracted {len(normalized_data['products'])} products")
            print("[DEBUG] Final normalized supplier_name:", normalized_data.get('supplier_name'))
            print("[DEBUG] Final normalized supplier_info:", normalized_data.get('supplier_info'))
            print("[DEBUG] Final normalized currency:", normalized_data.get('currency'))
            return normalized_data
            
        except json.JSONDecodeError as e:
            print(f"JSON parsing error: {e}")
            print(f"Raw response that failed: {ai_response[:200]}...")
            return _create_fallback_response(pdf_text)
            
    except Exception as e:
        print(f"OpenAI API error: {e}")
        import traceback
        traceback.print_exc()
        return _create_error_response(str(e))
    
def _build_enhanced_prompt(pdf_text: str, currency_hints: list = None) -> str:
    """Build an enhanced prompt for comprehensive supplier and product extraction"""
    
    currency_instruction = ""
    if currency_hints:
        currency_instruction = f"\n**IMPORTANT CURRENCY DETECTED**: The document contains these currency symbols: {', '.join(currency_hints)}. USE THESE CURRENCIES, DO NOT DEFAULT TO £!"
    
    return f"""
Extract supplier and product information from this invoice/document.{currency_instruction}

CRITICAL: Extract COMPLETE supplier information from the document header (works for ANY country):
- Company name (e.g., "MAC Global Ventures Ltd", "ABC Corp", "XYZ GmbH")
- Full address (any format - street, city, state, country, postal/zip code)
- Phone number (any international format - +44, +1, +91, +86, 020, 800, etc.)
- Email address (any format containing @)
- VAT/Tax/GST number (VAT, TIN, GST, Tax ID, etc.)
- Company Registration number (Company Reg, Corp ID, Registration No., etc.)

EXTRACTION STRATEGY (INTERNATIONAL):
1. Look at the TOP of the document for company letterhead/header
2. Extract the business name (usually largest/first text)
3. Extract complete address below company name (may span multiple lines)
4. Find phone numbers: +country_code, area_codes, local numbers, toll-free
5. Find email addresses: any text containing @ symbol
6. Find tax numbers: VAT, TIN, GST, Tax ID, Registration numbers
7. Find company registration: Corp ID, Reg No., Company Number
8. Extract COMPLETE packaging details: pack size, carton size, box quantity, bulk quantity
9. **CRITICAL CURRENCY DETECTION**: 
   - CAREFULLY scan the ENTIRE document for currency symbols and prices
   - Look for: $, €, ¥, ₹, ₽, CAD, AUD, CHF, SEK, NOK, DKK, PLN, CZK, HUF, etc.
   - Find currency codes: USD, EUR, JPY, INR, CAD, AUD, CHF, SEK, NOK, DKK, PLN, CZK, HUF, etc.
   - DO NOT default to £ unless you clearly see £ or GBP symbols
   - If you see $, it could be USD, CAD, AUD - look for context clues
   - Extract the EXACT currency used in the document prices

DOCUMENT:
{pdf_text}

Return JSON in exactly this format (ALL FIELDS ARE REQUIRED):
{{
    "supplier_name": "[COMPANY NAME FROM DOCUMENT HEADER]",
    "currency": "[MANDATORY FIELD - EXACT CURRENCY FROM DOCUMENT - NEVER OMIT THIS FIELD]",
    "supplier": {{
        "name": "[SAME COMPANY NAME]",
        "address": "[COMPLETE ADDRESS - all lines combined with proper spacing]",
        "email": "[EMAIL ADDRESS if found, otherwise null]",
        "phone": "[PHONE NUMBER in any format if found, otherwise null]",
        "vat_number": "[VAT/TAX/GST NUMBER if found, otherwise null]",
        "company_registration": "[COMPANY/CORP REGISTRATION if found, otherwise null]",
        "contact_person": "[CONTACT PERSON NAME if found, otherwise null]"
    }},
    "products": [
        {{
            "name": "Product name",
            "description": "Full product description with pack sizes",
            "price": 0.00,
            "original_price": 0.00,
            "currency": "[MANDATORY - MUST MATCH DOCUMENT CURRENCY FIELD ABOVE]",
            "unit_price": 0.00,            "pack_price": 0.00,
            "pack_quantity": 1,            "quantity": 1,
            "size": "EXTRACT: pack of X, box of Y, carton quantity, bulk size, etc.",
            "packaging_details": "Any carton/packaging/box details and quantities"
        }}

**CRITICAL PRICING INSTRUCTIONS:**
- "unit_price": Extract the PACK/BOX PRICE as shown in the document (the price you pay per pack/box)
- "pack_price": Extract the same pack/box price as above  
- "pack_quantity": Extract how many individual items are in each pack/box
- For "8oz Paper Cup pack of 50" priced at $13.08:
  * "unit_price": 13.08, "pack_price": 13.08, "pack_quantity": 50
- For "1000 pcs pack" priced at $50.00:
  * "unit_price": 50.00, "pack_price": 50.00, "pack_quantity": 1000
- DO NOT calculate per-piece prices - extract the price per pack/box as the unit_price
- The "unit_price" should be the price you pay for one complete pack/box
- If document shows "$13.08 for 8oz cups (pack of 50)", extract unit_price: 13.08
    ]
}}

**ABSOLUTE REQUIREMENTS:**
1. The "currency" field is MANDATORY and must NEVER be omitted
2. If you see $, it could be USD, CAD, AUD - look for country context
3. NEVER use £ unless you explicitly see £ or "GBP" in the document
4. The currency field should contain the EXACT symbol or code found in the document

EXTRACTION RULES (INTERNATIONAL FLEXIBLE):
1. SUPPLIER DETAILS are CRITICAL - extract ALL available contact info from document header
2. **CURRENCY**: Identify currency symbols (£, $, €, ¥, ₹, ¢, ₽, ₴, ₦, ₨, ₩, ₪, ₫, ₱, ₡, ₸, etc.) or codes (GBP, USD, EUR, JPY, INR, CAD, AUD, etc.)
3. Phone numbers: Accept ANY format (+country, area code, local, toll-free)
4. Addresses: Combine all address lines with proper spacing
5. Email: Any text containing @ symbol
6. Tax numbers: VAT, TIN, GST, Tax ID, Registration No., etc.
7. Company registration: Corp ID, Reg No., Company Number, etc.
8. SIZE/PACKAGING: Extract "pack of 25", "250 Pcs in a carton", "box of 100", etc.
9. Extract product descriptions WORD-FOR-WORD including all packaging info
10. **PRICING**: Store original_price in detected currency, price as numerical value
11. Return valid JSON only
12. Use null (not "Unknown" or "Not provided") if information is truly not found

CRITICAL: 
- Extract ALL packaging, size, and quantity information into the "size" field
- **DETECT CURRENCY SYMBOLS/CODES** from prices throughout the document
- Store original currency information for each product
"""

def _parse_json_response(ai_response: str) -> Dict[str, Any]:
    """Extract and parse JSON from AI response"""
    
    # Clean response to extract JSON
    if "```json" in ai_response:
        json_start = ai_response.find("```json") + 7
        json_end = ai_response.find("```", json_start)
        json_str = ai_response[json_start:json_end].strip()
    elif "{" in ai_response:
        json_start = ai_response.find("{")
        json_end = ai_response.rfind("}") + 1
        json_str = ai_response[json_start:json_end]
    else:
        json_str = ai_response
    
    print(f"[ai_extractor] Parsing JSON: {json_str[:200]}...")
    return json.loads(json_str)

def _normalize_extracted_data(data: Dict[str, Any]) -> Dict[str, Any]:
    """Normalize and validate extracted data with comprehensive product descriptions"""
    
    # Debug: Print what AI extracted for supplier
    print(f"🔍 SUPPLIER EXTRACTION DEBUG (INTERNATIONAL):")
    print(f"   Raw AI response keys: {list(data.keys())}")
    print(f"   supplier_name: {data.get('supplier_name')}")
    
    # Check if supplier is nested properly
    supplier_data = data.get('supplier', {})
    if isinstance(supplier_data, dict):
        print(f"   supplier.name: {supplier_data.get('name')}")
        print(f"   supplier.address: {supplier_data.get('address')}")
        print(f"   supplier.phone: {supplier_data.get('phone')}")
        print(f"   supplier.email: {supplier_data.get('email')}")
        print(f"   supplier.vat_number: {supplier_data.get('vat_number')}")
        print(f"   supplier.company_registration: {supplier_data.get('company_registration')}")
        print(f"   supplier.contact_person: {supplier_data.get('contact_person')}")
    else:
        print(f"   supplier (non-dict): {supplier_data}")
    
    print(f"   Checking alternative field names:")
    print(f"   - address: {data.get('address')}")
    print(f"   - phone/telephone: {data.get('phone')} / {data.get('telephone')}")
    print(f"   - email: {data.get('email')}")
    print(f"   - vat_number/tax_id/tin: {data.get('vat_number')} / {data.get('tax_id')} / {data.get('tin')}")
    print(f"   - company_registration/corp_id: {data.get('company_registration')} / {data.get('corp_id')}")
    print(f"   - contact_person: {data.get('contact_person')}")
    
    # Extract final values with multiple international fallbacks
    final_address = (
        supplier_data.get('address') or data.get('address') or 
        data.get('supplier_address') or data.get('business_address') or
        'Not provided'
    )
    
    final_phone = (
        supplier_data.get('phone') or data.get('phone') or 
        data.get('telephone') or data.get('tel') or data.get('mobile') or
        'Not provided'  
    )
    
    final_email = (
        supplier_data.get('email') or data.get('email') or
        data.get('email_address') or data.get('contact_email') or
        'Not provided'
    )
    
    final_vat = (
        supplier_data.get('vat_number') or data.get('vat_number') or
        data.get('tax_id') or data.get('tin') or data.get('gst_number') or
        data.get('vat') or data.get('tax_number') or
        'Not provided'
    )
    
    final_company_reg = (
        supplier_data.get('company_registration') or data.get('company_registration') or
        data.get('corp_id') or data.get('registration_number') or 
        data.get('company_number') or data.get('reg_no') or
        'Not provided'
    )
    
    final_contact = (
        supplier_data.get('contact_person') or data.get('contact_person') or
        data.get('contact') or data.get('representative') or
        'Not provided'
    )
    
    print(f"🌍 FINAL EXTRACTED VALUES (INTERNATIONAL):")
    print(f"   ✅ Address: {final_address}")
    print(f"   ✅ Phone: {final_phone}")
    print(f"   ✅ Email: {final_email}")
    print(f"   ✅ VAT/Tax: {final_vat}")
    print(f"   ✅ Company Reg: {final_company_reg}")
    print(f"   ✅ Contact: {final_contact}")
    
    # Extract currency information with debug
    extracted_currency = data.get("currency", "£")
    print(f"🔍 CURRENCY EXTRACTION DEBUG:")
    print(f"   Raw currency from AI: {extracted_currency}")
    
    # Try multiple field names for supplier
    supplier_name = (
        data.get("supplier_name") or 
        data.get("supplier", {}).get("name") if isinstance(data.get("supplier"), dict) else data.get("supplier") or
        data.get("company_name") or 
        data.get("vendor_name") or
        "Unknown Supplier"
    )
    
    print(f"🔍 FINAL EXTRACTED SUPPLIER NAME: {supplier_name}")
    
    # Ensure all main data fields are dictionaries, not strings
    supplier_info = data.get("supplier_info") or data.get("supplier") or {}
    if isinstance(supplier_info, str):
        supplier_info = {}
        
    document_info = data.get("document_info") or {}
    if isinstance(document_info, str):
        document_info = {}
        
    products = data.get("products") or []
    if not isinstance(products, list):
        products = []
        
    commercial_terms = data.get("commercial_terms") or {}
    if isinstance(commercial_terms, str):
        commercial_terms = {}
        
    shipping_info = data.get("shipping_info") or {}
    if isinstance(shipping_info, str):
        shipping_info = {}
        
    totals = data.get("totals") or {}
    if isinstance(totals, str):
        totals = {}
    
    # Normalize products with comprehensive descriptions
    normalized_products = []
    for product in products:
        # Ensure these are dictionaries, not strings
        pricing = product.get("pricing") or {}
        if isinstance(pricing, str):
            pricing = {}
            
        specifications = product.get("specifications") or {}
        if isinstance(specifications, str):
            specifications = {}
            
        availability = product.get("availability") or {}
        if isinstance(availability, str):
            availability = {}
            
        packaging_details = product.get("packaging_details") or {}
        if isinstance(packaging_details, str):
            packaging_details = {}
        
        # Get currency for this product (fallback to document currency)
        product_currency = product.get("currency") or extracted_currency
        
        # Extract pack pricing fields
        pack_price = _safe_number(product.get("pack_price")) or _safe_number(product.get("price"))
        pack_quantity = _safe_number(product.get("pack_quantity"), 1)
        extracted_unit_price = _safe_number(product.get("unit_price")) or _safe_number(pricing.get("unit_price")) or _safe_number(product.get("price"))
        
        # Use the pack price as the unit price (price per pack/box)
        final_unit_price = pack_price or extracted_unit_price

        normalized_product = {
            "name": product.get("name") or "Unknown Product",
            "full_description": product.get("full_description") or product.get("description") or "No description available",
            "short_description": product.get("short_description") or _create_short_description(product.get("full_description", "")),
            "sku": product.get("sku") or "Unknown",
            "manufacturer_code": product.get("manufacturer_code") or "Unknown",
            "category": product.get("category") or "Unknown",
            "brand": product.get("brand") or "Unknown",
            "model": product.get("model") or "Unknown",
            "size": (
                product.get("size") or 
                product.get("pack_size") or
                product.get("packaging_details") or
                packaging_details.get("pack_size") or
                packaging_details.get("carton_quantity") or
                "Unknown"
            ),
            "packaging_details": {
                "pack_size": packaging_details.get("pack_size") or product.get("size") or "Unknown",
                "carton_quantity": packaging_details.get("carton_quantity") or "Unknown",
                "bulk_quantity": packaging_details.get("bulk_quantity") or "Unknown",
                "packaging_type": packaging_details.get("packaging_type") or "Unknown"
            },
            "specifications": {
                "material": specifications.get("material") or "Unknown",
                "dimensions": specifications.get("dimensions") or "Unknown", 
                "weight": specifications.get("weight") or "Unknown",
                "color": specifications.get("color") or "Unknown",
                "grade": specifications.get("grade") or "Unknown",
                "certification": specifications.get("certification") or "Unknown",
                "origin": specifications.get("origin") or "Unknown"
            },
            "pricing": {
                "unit_rate": final_unit_price,
                "rate_per": pricing.get("rate_per") or "pack",
                "total_line_cost": _safe_number(pricing.get("total_line_cost")),
                "currency": pricing.get("currency") or product_currency,
                "quantity_ordered": _safe_number(pricing.get("quantity_ordered"), 1),
                "unit_of_measure": pricing.get("unit_of_measure") or "Unknown",
                "discount_percentage": _safe_number(pricing.get("discount_percentage")),
                "discount_amount": _safe_number(pricing.get("discount_amount")),
                "vat_rate": pricing.get("vat_rate") or "Unknown",
                "vat_amount": _safe_number(pricing.get("vat_amount")),
                # Legacy fields for backward compatibility
                "unit_price": final_unit_price,
                "quantity": _safe_number(pricing.get("quantity_ordered"), 1) or _safe_number(product.get("quantity"), 1),
                "unit": pricing.get("unit_of_measure") or pricing.get("unit") or "Unknown",
                "total_price": _safe_number(pricing.get("total_line_cost")) or _safe_number(pricing.get("total_price"))
            },
            "availability": {
                "stock_status": availability.get("stock_status") or "Unknown",
                "lead_time": availability.get("lead_time") or "Unknown",
                "minimum_order": availability.get("minimum_order") or "Unknown"
            },
            "additional_info": product.get("additional_info") or "None",
            # Legacy fields for backward compatibility
            "description": product.get("full_description") or product.get("description") or "No description available",
            "price": final_unit_price,
            "original_price": final_unit_price,
            "currency": product_currency,
            "unit_price": final_unit_price,
            "pack_price": pack_price,
            "pack_quantity": pack_quantity,
            "quantity": _safe_number(product.get("quantity"), 1) or _safe_number(pricing.get("quantity_ordered"), 1)
        }
        normalized_products.append(normalized_product)
    
    return {
        "supplier_name": supplier_name,
        "currency": extracted_currency,  # Add the currency field here!
        "supplier_info": {
            "address": final_address,
            "phone": final_phone, 
            "email": final_email,
            "vat_number": final_vat,
            "company_registration": final_company_reg,
            "website": supplier_info.get("website") or "Not provided",
            "contact_person": final_contact,
            "department": supplier_info.get("department") or "Not provided"
        },
        "document_info": {
            "document_type": document_info.get("document_type") or "Unknown",
            "document_number": document_info.get("document_number") or "Unknown",
            "issue_date": document_info.get("issue_date") or "Unknown",
            "due_date": document_info.get("due_date") or "Unknown",
            "order_number": document_info.get("order_number") or "Unknown",
            "delivery_note": document_info.get("delivery_note") or "Unknown"
        },
        "products": normalized_products,
        "commercial_terms": {
            "payment_terms": commercial_terms.get("payment_terms") or "Unknown",
            "delivery_terms": commercial_terms.get("delivery_terms") or "Unknown",
            "warranty": commercial_terms.get("warranty") or "Unknown",
            "return_policy": commercial_terms.get("return_policy") or "Unknown",
            "validity": commercial_terms.get("validity") or "Unknown"
        },
        "shipping_info": {
            "delivery_address": shipping_info.get("delivery_address") or "Unknown",
            "shipping_method": shipping_info.get("shipping_method") or "Unknown",
            "shipping_cost": _safe_number(shipping_info.get("shipping_cost")),
            "tracking_number": shipping_info.get("tracking_number") or "Unknown",
            "expected_delivery": shipping_info.get("expected_delivery") or "Unknown"
        },
        "totals": {
            "subtotal": _safe_number(totals.get("subtotal")),
            "discount_total": _safe_number(totals.get("discount_total")),
            "shipping_total": _safe_number(totals.get("shipping_total")),
            "vat_total": _safe_number(totals.get("vat_total")),
            "total_amount": _safe_number(totals.get("total_amount")),
            "currency": totals.get("currency") or "Unknown"
        },
        # Legacy fields for backward compatibility  
        "document_type": document_info.get("document_type") or "Unknown",
        "document_number": document_info.get("document_number") or "Unknown",
        "total_amount": _safe_number(totals.get("total_amount"))
    }

def _create_short_description(full_description: str) -> str:
    """Create a short description from full description"""
    if not full_description or full_description == "No description available":
        return "No description available"
    
    # Take first sentence or first 100 characters
    sentences = re.split(r'[.!?]', full_description)
    if sentences and len(sentences[0]) > 0:
        first_sentence = sentences[0].strip()
        if len(first_sentence) <= 100:
            return first_sentence + "."
        else:
            return first_sentence[:97] + "..."
    
    return full_description[:97] + "..." if len(full_description) > 100 else full_description

def _safe_number(value: Any, default: float = 0.0) -> float:
    """Convert values to float safely"""
    try:
        if value is None or value == "Unknown" or value == "":
            return default
        return float(value)
    except (TypeError, ValueError):
        return default

def _create_fallback_response(pdf_text: str) -> Dict[str, Any]:
    """Create comprehensive fallback response when AI parsing fails"""
    
    print("⚠️ WARNING: Using fallback response - AI extraction failed!")
    print(f"📄 PDF text length: {len(pdf_text)} chars")
    
    lines = pdf_text.split('\n')
    supplier_name = "Unknown Supplier"
    
    print(f"🔍 Trying to extract supplier from first 10 lines:")
    
    # Try to extract company name from first few lines
    for i, line in enumerate(lines[:10]):
        line = line.strip()
        print(f"   Line {i+1}: '{line}'")
        if len(line) > 3 and not line.isdigit():
            skip_words = ['invoice', 'bill', 'date', 'to:', 'vat', 'tax', 'total', 'amount', 'page', 'www']
            if not any(skip_word in line.lower() for skip_word in skip_words):
                supplier_name = line[:100]
                print(f"✅ Found potential supplier name: '{supplier_name}'")
                break
    
    print(f"🏷️ Final supplier_name: '{supplier_name}'")
    
    return {
        "supplier_name": supplier_name,
        "supplier_info": {
            "address": "Manual review required",
            "phone": "Manual review required",
            "email": "Manual review required",
            "vat_number": "Manual review required",
            "company_registration": "Manual review required",
            "website": "Manual review required",
            "contact_person": "Manual review required",
            "department": "Manual review required"
        },
        "document_info": {
            "document_type": "Unknown",
            "document_number": "Manual review required",
            "issue_date": "Manual review required",
            "due_date": "Manual review required",
            "order_number": "Manual review required",
            "delivery_note": "Manual review required"
        },
        "products": [
            {
                "name": "Manual review required - AI parsing failed",
                "full_description": "Please review document manually to extract product descriptions",
                "short_description": "Manual review required",
                "sku": "Unknown",
                "manufacturer_code": "Unknown",
                "category": "Unknown", 
                "brand": "Unknown",
                "model": "Unknown",
                "specifications": {
                    "material": "Unknown",
                    "dimensions": "Unknown",
                    "weight": "Unknown",
                    "color": "Unknown",
                    "grade": "Unknown",
                    "certification": "Unknown",
                    "origin": "Unknown"
                },
                "pricing": {
                    "unit_price": 0.0,
                    "currency": "Unknown",
                    "quantity": 1,
                    "unit": "Unknown",
                    "total_price": 0.0,
                    "discount_percentage": 0.0,
                    "discount_amount": 0.0,
                    "vat_rate": "Unknown",
                    "vat_amount": 0.0
                },
                "availability": {
                    "stock_status": "Unknown",
                    "lead_time": "Unknown",
                    "minimum_order": "Unknown"
                },
                "additional_info": "AI extraction failed - manual review required",
                "description": "Please review document manually",
                "price": 0.0
            }
        ],
        "commercial_terms": {
            "payment_terms": "Manual review required",
            "delivery_terms": "Manual review required",
            "warranty": "Manual review required",
            "return_policy": "Manual review required",
            "validity": "Manual review required"
        },
        "shipping_info": {
            "delivery_address": "Manual review required",
            "shipping_method": "Manual review required", 
            "shipping_cost": 0.0,
            "tracking_number": "Manual review required",
            "expected_delivery": "Manual review required"
        },
        "totals": {
            "subtotal": 0.0,
            "discount_total": 0.0,
            "shipping_total": 0.0,
            "vat_total": 0.0,
            "total_amount": 0.0,
            "currency": "Unknown"
        },
        "document_type": "Unknown",
        "document_number": "Manual review required", 
        "total_amount": 0.0
    }

def _create_error_response(error_msg: str) -> Dict[str, Any]:
    """Create comprehensive error response when API call fails"""
    
    truncated_error = error_msg[:50] + "..." if len(error_msg) > 50 else error_msg
    
    return {
        "supplier_name": f"❌ AI Error: {truncated_error}",
        "supplier_info": {
            "address": "Error - API call failed",
            "phone": "Error - API call failed",
            "email": "Error - API call failed", 
            "vat_number": "Error - API call failed",
            "company_registration": "Error - API call failed",
            "website": "Error - API call failed",
            "contact_person": "Error - API call failed",
            "department": "Error - API call failed"
        },
        "document_info": {
            "document_type": "Error",
            "document_number": "Error - API call failed",
            "issue_date": "Error - API call failed",
            "due_date": "Error - API call failed",
            "order_number": "Error - API call failed",
            "delivery_note": "Error - API call failed"
        },
        "products": [
            {
                "name": "AI extraction failed",
                "full_description": f"Error occurred during AI extraction: {error_msg}",
                "short_description": "AI extraction failed",
                "sku": "Error",
                "manufacturer_code": "Error",
                "category": "Error",
                "brand": "Error", 
                "model": "Error",
                "specifications": {
                    "material": "Error",
                    "dimensions": "Error",
                    "weight": "Error",
                    "color": "Error",
                    "grade": "Error",
                    "certification": "Error",
                    "origin": "Error"
                },
                "pricing": {
                    "unit_price": 0.0,
                    "currency": "Error",
                    "quantity": 1,
                    "unit": "Error",
                    "total_price": 0.0,
                    "discount_percentage": 0.0,
                    "discount_amount": 0.0,
                    "vat_rate": "Error",
                    "vat_amount": 0.0
                },
                "availability": {
                    "stock_status": "Error",
                    "lead_time": "Error", 
                    "minimum_order": "Error"
                },
                "additional_info": f"API Error: {error_msg}",
                "description": f"Error: {error_msg}",
                "price": 0.0
            }
        ],
        "commercial_terms": {
            "payment_terms": "Error - API call failed",
            "delivery_terms": "Error - API call failed", 
            "warranty": "Error - API call failed",
            "return_policy": "Error - API call failed",
            "validity": "Error - API call failed"
        },
        "shipping_info": {
            "delivery_address": "Error - API call failed",
            "shipping_method": "Error - API call failed",
            "shipping_cost": 0.0,
            "tracking_number": "Error - API call failed",
            "expected_delivery": "Error - API call failed"
        },
        "totals": {
            "subtotal": 0.0,
            "discount_total": 0.0,
            "shipping_total": 0.0,
            "vat_total": 0.0,
            "total_amount": 0.0,
            "currency": "Error"
        },
        "document_type": "Error",
        "document_number": "Error - API call failed",
        "total_amount": 0.0
    }

