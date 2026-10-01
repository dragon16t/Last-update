#!/usr/bin/env python3
"""
Focused Backend Test Suite - 3 Critical Tests Only
Tests: AI skin analysis (Gemini), Razorpay order creation, Product catalog
"""
import requests
import sys
import json
import base64
from typing import Dict, Any

# Base URL from frontend/.env
BASE_URL = "https://ecom-preview-16.preview.emergentagent.com/api"

class Colors:
    GREEN = '\033[92m'
    RED = '\033[91m'
    YELLOW = '\033[93m'
    BLUE = '\033[94m'
    END = '\033[0m'

def print_success(msg: str):
    print(f"{Colors.GREEN}✓ {msg}{Colors.END}")

def print_error(msg: str):
    print(f"{Colors.RED}✗ {msg}{Colors.END}")

def print_warning(msg: str):
    print(f"{Colors.YELLOW}⚠ {msg}{Colors.END}")

def print_info(msg: str):
    print(f"{Colors.BLUE}ℹ {msg}{Colors.END}")

class TestResults:
    def __init__(self):
        self.passed = 0
        self.failed = 0
        self.errors = []
        self.details = []

    def add_pass(self, test_name: str, details: str = ""):
        self.passed += 1
        self.details.append({"test": test_name, "status": "PASS", "details": details})

    def add_fail(self, test_name: str, error: str):
        self.failed += 1
        self.errors.append(error)
        self.details.append({"test": test_name, "status": "FAIL", "error": error})

    def summary(self):
        total = self.passed + self.failed
        print("\n" + "="*80)
        print(f"TEST SUMMARY: {self.passed}/{total} passed")
        if self.failed > 0:
            print(f"{Colors.RED}Failed: {self.failed}{Colors.END}")
            print("\nFailed Tests:")
            for error in self.errors:
                print(f"  - {error}")
        print("="*80)
        return self.failed == 0

results = TestResults()

def download_image_as_base64(url: str) -> str:
    """Download image from URL and convert to base64 data URL"""
    print_info(f"Downloading image from: {url}")
    try:
        response = requests.get(url, timeout=15)
        if response.status_code == 200:
            # Convert to base64
            image_data = base64.b64encode(response.content).decode('utf-8')
            # Create data URL (assuming JPEG)
            data_url = f"data:image/jpeg;base64,{image_data}"
            print_success(f"Image downloaded successfully ({len(response.content)} bytes)")
            return data_url
        else:
            print_error(f"Failed to download image: HTTP {response.status_code}")
            return None
    except Exception as e:
        print_error(f"Exception downloading image: {str(e)}")
        return None

def test_ai_skin_analysis():
    """Test 1: POST /api/routine/analyze - AI skin analysis with Gemini"""
    test_name = "AI Skin Analysis (Gemini)"
    print(f"\n{Colors.BLUE}{'='*80}")
    print(f"TEST 1: {test_name}")
    print(f"{'='*80}{Colors.END}")
    
    url = f"{BASE_URL}/routine/analyze"
    print(f"POST {url}")
    
    # Try first face image
    face_url_1 = "https://images.unsplash.com/photo-1544005313-94ddf0286df2?w=400"
    image_data = download_image_as_base64(face_url_1)
    
    if not image_data:
        # Try alternative face image
        print_warning("Trying alternative face image...")
        face_url_2 = "https://images.unsplash.com/photo-1494790108377-be9c29b29330?w=400"
        image_data = download_image_as_base64(face_url_2)
        
        if not image_data:
            error_msg = f"{test_name} - Failed to download face images"
            print_error(error_msg)
            results.add_fail(test_name, error_msg)
            return
    
    payload = {"front": image_data}
    print_info(f"Payload size: {len(json.dumps(payload))} bytes")
    
    try:
        print_info("Sending request to Gemini AI endpoint...")
        response = requests.post(url, json=payload, timeout=30)
        print(f"Status: {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            print_info(f"Response keys: {list(data.keys())}")
            
            # Validate response structure
            required_fields = ["success", "is_human", "skin_score"]
            missing_fields = [f for f in required_fields if f not in data]
            
            if missing_fields:
                error_msg = f"{test_name} - Missing fields: {missing_fields}"
                print_error(error_msg)
                results.add_fail(test_name, error_msg)
                return
            
            # Check values
            skin_score = data.get("skin_score")
            is_human = data.get("is_human")
            recommended_concerns = data.get("recommended_concerns", [])
            
            print_info(f"Skin Score: {skin_score}")
            print_info(f"Is Human: {is_human}")
            print_info(f"Recommended Concerns: {recommended_concerns}")
            print_info(f"Primary Concern: {data.get('primary_concern')}")
            
            if is_human and isinstance(skin_score, int) and skin_score > 0:
                details = f"Skin Score: {skin_score}, Concerns: {recommended_concerns}"
                print_success(f"{test_name} - PASSED - Gemini AI analysis working correctly")
                results.add_pass(test_name, details)
            else:
                error_msg = f"{test_name} - Invalid response values (is_human={is_human}, skin_score={skin_score})"
                print_error(error_msg)
                results.add_fail(test_name, error_msg)
                
        elif response.status_code == 422:
            # Face not recognized - try alternative
            print_warning("Face not recognized (422), trying alternative image...")
            face_url_2 = "https://images.unsplash.com/photo-1494790108377-be9c29b29330?w=400"
            image_data_2 = download_image_as_base64(face_url_2)
            
            if image_data_2:
                payload_2 = {"front": image_data_2}
                response_2 = requests.post(url, json=payload_2, timeout=30)
                print(f"Retry Status: {response_2.status_code}")
                
                if response_2.status_code == 200:
                    data_2 = response_2.json()
                    skin_score = data_2.get("skin_score")
                    is_human = data_2.get("is_human")
                    recommended_concerns = data_2.get("recommended_concerns", [])
                    
                    print_info(f"Skin Score: {skin_score}")
                    print_info(f"Is Human: {is_human}")
                    print_info(f"Recommended Concerns: {recommended_concerns}")
                    
                    if is_human and isinstance(skin_score, int) and skin_score > 0:
                        details = f"Skin Score: {skin_score}, Concerns: {recommended_concerns}"
                        print_success(f"{test_name} - PASSED (with retry) - Gemini AI analysis working correctly")
                        results.add_pass(test_name, details)
                    else:
                        error_msg = f"{test_name} - Invalid response values after retry"
                        print_error(error_msg)
                        results.add_fail(test_name, error_msg)
                else:
                    error_msg = f"{test_name} - Failed after retry: HTTP {response_2.status_code}"
                    print_error(error_msg)
                    try:
                        error_detail = response_2.json()
                        print_info(f"Error detail: {json.dumps(error_detail, indent=2)}")
                    except:
                        pass
                    results.add_fail(test_name, error_msg)
            else:
                error_msg = f"{test_name} - Face not recognized and alternative image download failed"
                print_error(error_msg)
                results.add_fail(test_name, error_msg)
                
        elif response.status_code == 500:
            # Check for API key or quota error
            try:
                error_data = response.json()
                error_detail = error_data.get("detail", "")
                print_error(f"500 Error Detail: {error_detail}")
                
                if "API" in error_detail or "key" in error_detail.lower() or "quota" in error_detail.lower():
                    error_msg = f"{test_name} - API Key/Quota Error: {error_detail}"
                else:
                    error_msg = f"{test_name} - Server Error (500): {error_detail}"
                    
                print_error(error_msg)
                results.add_fail(test_name, error_msg)
            except:
                error_msg = f"{test_name} - Server Error (500) - Unable to parse error detail"
                print_error(error_msg)
                results.add_fail(test_name, error_msg)
        else:
            error_msg = f"{test_name} - Unexpected status {response.status_code}"
            print_error(error_msg)
            try:
                error_data = response.json()
                print_info(f"Response: {json.dumps(error_data, indent=2)}")
            except:
                pass
            results.add_fail(test_name, error_msg)
            
    except requests.exceptions.Timeout:
        error_msg = f"{test_name} - Request timeout (>30s)"
        print_error(error_msg)
        results.add_fail(test_name, error_msg)
    except Exception as e:
        error_msg = f"{test_name} - Exception: {str(e)}"
        print_error(error_msg)
        results.add_fail(test_name, error_msg)

def test_razorpay_order():
    """Test 2: POST /api/create-razorpay-order with amount 199"""
    test_name = "Razorpay Order Creation (₹199)"
    print(f"\n{Colors.BLUE}{'='*80}")
    print(f"TEST 2: {test_name}")
    print(f"{'='*80}{Colors.END}")
    
    url = f"{BASE_URL}/create-razorpay-order"
    payload = {"amount": 199}
    print(f"POST {url}")
    print(f"Payload: {json.dumps(payload)}")
    
    try:
        response = requests.post(url, json=payload, timeout=10)
        print(f"Status: {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            print_info(f"Response: {json.dumps(data, indent=2)}")
            
            # Validate response structure
            order_id = data.get("id", "")
            amount = data.get("amount")
            currency = data.get("currency", "")
            
            print_info(f"Order ID: {order_id}")
            print_info(f"Amount: {amount} paise")
            print_info(f"Currency: {currency}")
            
            # Validate: order ID starts with "order_", amount is 19900 paise (₹199), currency is INR
            if order_id.startswith("order_") and amount == 19900 and currency == "INR":
                details = f"Order ID: {order_id}, Amount: ₹{amount/100}, Currency: {currency}"
                print_success(f"{test_name} - PASSED - Razorpay LIVE order created successfully")
                results.add_pass(test_name, details)
            else:
                error_msg = f"{test_name} - Invalid response (id={order_id}, amount={amount}, currency={currency})"
                print_error(error_msg)
                results.add_fail(test_name, error_msg)
                
        elif response.status_code == 503:
            error_msg = f"{test_name} - Payment gateway not configured (503)"
            print_error(error_msg)
            results.add_fail(test_name, error_msg)
        else:
            error_msg = f"{test_name} - Unexpected status {response.status_code}"
            print_error(error_msg)
            try:
                error_data = response.json()
                print_info(f"Response: {json.dumps(error_data, indent=2)}")
            except:
                pass
            results.add_fail(test_name, error_msg)
            
    except Exception as e:
        error_msg = f"{test_name} - Exception: {str(e)}"
        print_error(error_msg)
        results.add_fail(test_name, error_msg)

def test_product_catalog():
    """Test 3: GET /api/products?niche=skin-care&page=1&limit=20 - Expect exactly 4 products"""
    test_name = "Product Catalog (4 products)"
    print(f"\n{Colors.BLUE}{'='*80}")
    print(f"TEST 3: {test_name}")
    print(f"{'='*80}{Colors.END}")
    
    url = f"{BASE_URL}/products?niche=skin-care&page=1&limit=20"
    print(f"GET {url}")
    
    try:
        response = requests.get(url, timeout=10)
        print(f"Status: {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            
            # Check if it's paginated response or plain array
            if isinstance(data, dict) and "items" in data:
                products = data.get("items", [])
                total = data.get("total", 0)
                print_info(f"Paginated response: {len(products)} items, total: {total}")
            elif isinstance(data, list):
                products = data
                print_info(f"Array response: {len(products)} items")
            else:
                error_msg = f"{test_name} - Invalid response format"
                print_error(error_msg)
                results.add_fail(test_name, error_msg)
                return
            
            # Validate exactly 4 products
            product_count = len(products)
            print_info(f"Product count: {product_count}")
            
            if product_count == 4:
                # List product names
                product_names = [p.get("name", "Unknown") for p in products]
                print_info(f"Products: {product_names}")
                
                details = f"4 products found: {', '.join(product_names[:2])}..."
                print_success(f"{test_name} - PASSED - Exactly 4 products returned")
                results.add_pass(test_name, details)
            else:
                error_msg = f"{test_name} - Expected 4 products, got {product_count}"
                print_error(error_msg)
                if product_count > 0:
                    product_names = [p.get("name", "Unknown") for p in products]
                    print_info(f"Products: {product_names}")
                results.add_fail(test_name, error_msg)
        else:
            error_msg = f"{test_name} - Unexpected status {response.status_code}"
            print_error(error_msg)
            results.add_fail(test_name, error_msg)
            
    except Exception as e:
        error_msg = f"{test_name} - Exception: {str(e)}"
        print_error(error_msg)
        results.add_fail(test_name, error_msg)

def main():
    print(f"\n{Colors.BLUE}{'='*80}")
    print("FOCUSED BACKEND TEST SUITE - 3 CRITICAL TESTS")
    print("Celesta Glow E-commerce Platform")
    print(f"Base URL: {BASE_URL}")
    print(f"{'='*80}{Colors.END}\n")
    
    # Test 1: AI Skin Analysis (Gemini)
    test_ai_skin_analysis()
    
    # Test 2: Razorpay Order Creation
    test_razorpay_order()
    
    # Test 3: Product Catalog
    test_product_catalog()
    
    # Print summary
    success = results.summary()
    
    # Print detailed results
    print(f"\n{Colors.BLUE}DETAILED RESULTS:{Colors.END}")
    for detail in results.details:
        status_color = Colors.GREEN if detail["status"] == "PASS" else Colors.RED
        print(f"{status_color}{detail['status']}{Colors.END} - {detail['test']}")
        if detail["status"] == "PASS" and "details" in detail:
            print(f"      {detail['details']}")
        elif detail["status"] == "FAIL" and "error" in detail:
            print(f"      {detail['error']}")
    
    return 0 if success else 1

if __name__ == "__main__":
    sys.exit(main())
