#!/usr/bin/env python3
"""
30-Day Skin Journey API Test
Focused test of the NEW journey endpoints with minimal credit usage
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

def print_info(msg: str):
    print(f"{Colors.BLUE}ℹ {msg}{Colors.END}")

class TestResults:
    def __init__(self):
        self.passed = 0
        self.failed = 0
        self.errors = []

    def add_pass(self, test_name: str):
        self.passed += 1
        print_success(f"PASSED: {test_name}")

    def add_fail(self, test_name: str, error: str):
        self.failed += 1
        self.errors.append(f"{test_name}: {error}")
        print_error(f"FAILED: {test_name} - {error}")

    def summary(self):
        total = self.passed + self.failed
        print("\n" + "="*70)
        print(f"TEST SUMMARY: {self.passed}/{total} passed")
        if self.failed > 0:
            print(f"{Colors.RED}Failed: {self.failed}{Colors.END}")
            print("\nFailed Tests:")
            for error in self.errors:
                print(f"  - {error}")
        print("="*70)
        return self.failed == 0

results = TestResults()

def download_image_as_data_url(url: str) -> str:
    """Download image and convert to base64 data URL"""
    try:
        print_info(f"Downloading image from: {url}")
        response = requests.get(url, timeout=15)
        if response.status_code == 200:
            b64 = base64.b64encode(response.content).decode('utf-8')
            data_url = f"data:image/jpeg;base64,{b64}"
            print_info(f"Image downloaded successfully ({len(response.content)} bytes)")
            return data_url
        else:
            print_error(f"Failed to download image: {response.status_code}")
            return ""
    except Exception as e:
        print_error(f"Exception downloading image: {str(e)}")
        return ""

def test_journey_start_valid_face(face_data_url: str) -> Dict[str, Any]:
    """
    Step 1: POST /api/journey/start with valid face image
    Expect: 200 JSON with journey data, analysis, Day-1 tasks
    """
    print(f"\n{Colors.BLUE}{'='*70}")
    print("STEP 1: POST /api/journey/start (Valid Face)")
    print(f"{'='*70}{Colors.END}")
    
    url = f"{BASE_URL}/journey/start"
    payload = {
        "photo": face_data_url,
        "goals": ["Clear Acne", "Brighten & Glow"],
        "gender": "female",
        "age": "25–34"
    }
    
    print_info(f"POST {url}")
    print_info(f"Payload: goals={payload['goals']}, gender={payload['gender']}, age={payload['age']}")
    
    try:
        response = requests.post(url, json=payload, timeout=30)
        print_info(f"Status: {response.status_code}")
        
        if response.status_code != 200:
            results.add_fail("Journey Start (Valid Face)", f"Expected 200, got {response.status_code}")
            try:
                error_data = response.json()
                print_error(f"Error response: {json.dumps(error_data, indent=2)}")
            except:
                print_error(f"Response text: {response.text[:500]}")
            return {"success": False, "journey_id": None}
        
        data = response.json()
        
        # Validate response structure
        required_fields = ["id", "analysis", "before_photo", "current_day", "total_days", "days"]
        missing_fields = [f for f in required_fields if f not in data]
        
        if missing_fields:
            results.add_fail("Journey Start (Valid Face)", f"Missing fields: {missing_fields}")
            return {"success": False, "journey_id": None}
        
        # Validate analysis
        analysis = data.get("analysis", {})
        if "skin_score" not in analysis:
            results.add_fail("Journey Start (Valid Face)", "Missing skin_score in analysis")
            return {"success": False, "journey_id": data.get("id")}
        
        skin_score = analysis.get("skin_score")
        print_info(f"Skin Score: {skin_score}")
        print_info(f"Summary: {analysis.get('summary', 'N/A')}")
        
        # Validate Day-1 tasks
        days = data.get("days", {})
        day1 = days.get("1", {})
        tasks = day1.get("tasks", [])
        
        if not tasks:
            results.add_fail("Journey Start (Valid Face)", "No Day-1 tasks generated")
            return {"success": False, "journey_id": data.get("id")}
        
        print_info(f"Day-1 Tasks: {len(tasks)} tasks")
        for i, task in enumerate(tasks, 1):
            print_info(f"  Task {i}: {task.get('title')} ({task.get('time')})")
        
        # Validate before_photo path
        before_photo = data.get("before_photo", "")
        if not before_photo.startswith("/api/uploads/journeys/"):
            results.add_fail("Journey Start (Valid Face)", f"Invalid before_photo path: {before_photo}")
            return {"success": False, "journey_id": data.get("id")}
        
        print_info(f"Before Photo: {before_photo}")
        print_info(f"Current Day: {data.get('current_day')}")
        print_info(f"Total Days: {data.get('total_days')}")
        
        # Validate current_day and total_days
        if data.get("current_day") != 1:
            results.add_fail("Journey Start (Valid Face)", f"Expected current_day=1, got {data.get('current_day')}")
            return {"success": False, "journey_id": data.get("id")}
        
        if data.get("total_days") != 30:
            results.add_fail("Journey Start (Valid Face)", f"Expected total_days=30, got {data.get('total_days')}")
            return {"success": False, "journey_id": data.get("id")}
        
        results.add_pass("Journey Start (Valid Face)")
        print_info(f"✓ Journey ID: {data.get('id')}")
        print_info(f"✓ Skin Score: {skin_score}")
        print_info(f"✓ Day-1 Tasks: {len(tasks)}")
        
        return {"success": True, "journey_id": data.get("id"), "data": data, "first_task_id": tasks[0].get("id") if tasks else None}
        
    except Exception as e:
        results.add_fail("Journey Start (Valid Face)", f"Exception: {str(e)}")
        return {"success": False, "journey_id": None}

def test_journey_start_invalid_face(non_face_data_url: str) -> Dict[str, Any]:
    """
    Step 2: POST /api/journey/start with non-face image (negative test)
    Expect: HTTP 422 with error message containing "not your face"
    """
    print(f"\n{Colors.BLUE}{'='*70}")
    print("STEP 2: POST /api/journey/start (Non-Face Image - Negative Test)")
    print(f"{'='*70}{Colors.END}")
    
    url = f"{BASE_URL}/journey/start"
    payload = {
        "photo": non_face_data_url,
        "goals": ["Clear Acne"],
        "gender": "female",
        "age": "25–34"
    }
    
    print_info(f"POST {url}")
    print_info("Payload: Using landscape/object image (should be rejected)")
    
    try:
        response = requests.post(url, json=payload, timeout=30)
        print_info(f"Status: {response.status_code}")
        
        if response.status_code != 422:
            results.add_fail("Journey Start (Non-Face Rejection)", f"Expected 422, got {response.status_code}")
            return {"success": False}
        
        data = response.json()
        detail = data.get("detail", "")
        print_info(f"Error message: {detail}")
        
        # Check if error message contains "not your face" or similar
        if "not your face" in detail.lower() or "face" in detail.lower():
            results.add_pass("Journey Start (Non-Face Rejection)")
            print_info(f"✓ Correctly rejected non-face image with message: {detail}")
            return {"success": True}
        else:
            results.add_fail("Journey Start (Non-Face Rejection)", f"Error message doesn't mention face: {detail}")
            return {"success": False}
        
    except Exception as e:
        results.add_fail("Journey Start (Non-Face Rejection)", f"Exception: {str(e)}")
        return {"success": False}

def test_submit_day(journey_id: str, day: int, face_data_url: str, task_id: str) -> Dict[str, Any]:
    """
    Step 3: POST /api/journey/{id}/day/1/submit
    Expect: 200 JSON with current_day=2 and Day-2 tasks populated
    """
    print(f"\n{Colors.BLUE}{'='*70}")
    print(f"STEP 3: POST /api/journey/{journey_id}/day/{day}/submit")
    print(f"{'='*70}{Colors.END}")
    
    url = f"{BASE_URL}/journey/{journey_id}/day/{day}/submit"
    payload = {
        "proof": face_data_url,
        "completed": [task_id] if task_id else []
    }
    
    print_info(f"POST {url}")
    print_info(f"Payload: proof=<face_image>, completed=[{task_id}]")
    
    try:
        response = requests.post(url, json=payload, timeout=30)
        print_info(f"Status: {response.status_code}")
        
        if response.status_code != 200:
            results.add_fail("Submit Day 1", f"Expected 200, got {response.status_code}")
            try:
                error_data = response.json()
                print_error(f"Error response: {json.dumps(error_data, indent=2)}")
            except:
                print_error(f"Response text: {response.text[:500]}")
            return {"success": False}
        
        data = response.json()
        
        # Check needs_payment
        needs_payment = data.get("needs_payment", False)
        print_info(f"Needs Payment: {needs_payment}")
        
        if needs_payment:
            results.add_fail("Submit Day 1", "needs_payment should be false for first 30 days")
            return {"success": False}
        
        # Get journey data
        journey = data.get("journey", {})
        if not journey:
            results.add_fail("Submit Day 1", "No journey data in response")
            return {"success": False}
        
        current_day = journey.get("current_day")
        print_info(f"Current Day: {current_day}")
        
        if current_day != 2:
            results.add_fail("Submit Day 1", f"Expected current_day=2, got {current_day}")
            return {"success": False}
        
        # Check Day-2 tasks
        days = journey.get("days", {})
        day2 = days.get("2", {})
        day2_tasks = day2.get("tasks", [])
        
        if not day2_tasks:
            results.add_fail("Submit Day 1", "No Day-2 tasks generated")
            return {"success": False}
        
        print_info(f"Day-2 Tasks: {len(day2_tasks)} tasks")
        for i, task in enumerate(day2_tasks, 1):
            print_info(f"  Task {i}: {task.get('title')} ({task.get('time')})")
        
        results.add_pass("Submit Day 1")
        print_info(f"✓ Current Day: {current_day}")
        print_info(f"✓ Day-2 Tasks: {len(day2_tasks)}")
        print_info(f"✓ Needs Payment: {needs_payment}")
        
        return {"success": True, "data": data}
        
    except Exception as e:
        results.add_fail("Submit Day 1", f"Exception: {str(e)}")
        return {"success": False}

def test_get_journey(journey_id: str) -> Dict[str, Any]:
    """
    Step 4: GET /api/journey/{id}
    Expect: 200 and current_day=2
    """
    print(f"\n{Colors.BLUE}{'='*70}")
    print(f"STEP 4: GET /api/journey/{journey_id}")
    print(f"{'='*70}{Colors.END}")
    
    url = f"{BASE_URL}/journey/{journey_id}"
    print_info(f"GET {url}")
    
    try:
        response = requests.get(url, timeout=10)
        print_info(f"Status: {response.status_code}")
        
        if response.status_code != 200:
            results.add_fail("Get Journey", f"Expected 200, got {response.status_code}")
            return {"success": False}
        
        data = response.json()
        current_day = data.get("current_day")
        print_info(f"Current Day: {current_day}")
        
        if current_day != 2:
            results.add_fail("Get Journey", f"Expected current_day=2, got {current_day}")
            return {"success": False}
        
        # Validate structure
        required_fields = ["id", "analysis", "before_photo", "current_day", "total_days", "days"]
        missing_fields = [f for f in required_fields if f not in data]
        
        if missing_fields:
            results.add_fail("Get Journey", f"Missing fields: {missing_fields}")
            return {"success": False}
        
        results.add_pass("Get Journey")
        print_info(f"✓ Current Day: {current_day}")
        print_info(f"✓ Journey data retrieved successfully")
        
        return {"success": True, "data": data}
        
    except Exception as e:
        results.add_fail("Get Journey", f"Exception: {str(e)}")
        return {"success": False}

def main():
    print(f"\n{Colors.BLUE}{'='*70}")
    print("30-DAY SKIN JOURNEY API TEST")
    print("Focused test with minimal credit usage")
    print(f"Base URL: {BASE_URL}")
    print(f"{'='*70}{Colors.END}\n")
    
    # Download test images
    print(f"\n{Colors.BLUE}Preparing Test Images...{Colors.END}")
    
    # Valid face image
    face_url = "https://images.unsplash.com/photo-1494790108377-be9c29b29330?w=400"
    face_data_url = download_image_as_data_url(face_url)
    
    if not face_data_url:
        print_error("Failed to download face image. Trying alternative...")
        face_url = "https://images.unsplash.com/photo-1544005313-94ddf0286df2?w=400"
        face_data_url = download_image_as_data_url(face_url)
        
        if not face_data_url:
            print_error("Failed to download face images. Cannot proceed with tests.")
            return 1
    
    # Non-face image (landscape/object)
    non_face_url = "https://images.unsplash.com/photo-1526178613658-3f1622045557?w=400"
    non_face_data_url = download_image_as_data_url(non_face_url)
    
    if not non_face_data_url:
        print_error("Failed to download non-face image. Skipping negative test.")
    
    # Run tests
    print(f"\n{Colors.BLUE}Starting Tests...{Colors.END}")
    
    # Step 1: Start journey with valid face
    result1 = test_journey_start_valid_face(face_data_url)
    journey_id = result1.get("journey_id")
    first_task_id = result1.get("first_task_id")
    
    if not journey_id:
        print_error("Cannot proceed with remaining tests without journey_id")
        results.summary()
        return 1
    
    # Step 2: Negative test - non-face image
    if non_face_data_url:
        test_journey_start_invalid_face(non_face_data_url)
    
    # Step 3: Submit Day 1
    result3 = test_submit_day(journey_id, 1, face_data_url, first_task_id)
    
    # Step 4: Get journey
    test_get_journey(journey_id)
    
    # Print summary
    success = results.summary()
    
    return 0 if success else 1

if __name__ == "__main__":
    sys.exit(main())
