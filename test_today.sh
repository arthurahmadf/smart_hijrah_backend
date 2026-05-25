#!/bin/bash

# Colors for output
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

BASE_URL="http://localhost:8000"

echo -e "${YELLOW}========================================${NC}"
echo -e "${YELLOW}Testing Smart Hijrah - Today Endpoints${NC}"
echo -e "${YELLOW}========================================${NC}"

# 1. REGISTER USER
echo -e "\n${YELLOW}[1] Register User${NC}"
REGISTER_RESPONSE=$(curl -s -X POST "$BASE_URL/user/create/" \
  -H "Content-Type: application/json" \
  -d '{
    "username": "testuser_'$(date +%s)'",
    "password": "test123",
    "nama": "Test User",
    "email": "test@example.com",
    "alamat": "Jakarta",
    "telepon": "08123456789"
  }')
echo $REGISTER_RESPONSE | python3 -m json.tool

# 2. LOGIN
echo -e "\n${YELLOW}[2] Login${NC}"
LOGIN_RESPONSE=$(curl -s -X POST "$BASE_URL/auth/login/" \
  -H "Content-Type: application/json" \
  -d '{
    "username": "testuser_'$(date +%s)'",
    "password": "test123"
  }')
echo $LOGIN_RESPONSE | python3 -m json.tool

# Extract token (assuming username from register)
read -p "Enter username from above: " USERNAME
read -sp "Enter password: " PASSWORD
echo ""

LOGIN_RESPONSE=$(curl -s -X POST "$BASE_URL/auth/login/" \
  -H "Content-Type: application/json" \
  -d "{
    \"username\": \"$USERNAME\",
    \"password\": \"$PASSWORD\"
  }")

ACCESS_TOKEN=$(echo $LOGIN_RESPONSE | python3 -c "import sys, json; print(json.load(sys.stdin).get('access', ''))" 2>/dev/null)

if [ -z "$ACCESS_TOKEN" ]; then
    echo -e "${RED}Failed to get access token${NC}"
    exit 1
fi

echo -e "${GREEN}Token obtained: ${ACCESS_TOKEN:0:50}...${NC}"

# 3. GET MY PROFILE
echo -e "\n${YELLOW}[3] Get My Profile${NC}"
curl -s -X GET "$BASE_URL/user/me/" \
  -H "Authorization: Bearer $ACCESS_TOKEN" | python3 -m json.tool

# 4. CREATE FEED WITH IMAGES (need actual image files)
echo -e "\n${YELLOW}[4] Create Feed (without images first)${NC}"
CREATE_FEED_RESPONSE=$(curl -s -X POST "$BASE_URL/feed/create/" \
  -H "Authorization: Bearer $ACCESS_TOKEN" \
  -F "caption=Test feed from API" \
  -F "location=Jakarta")
echo $CREATE_FEED_RESPONSE | python3 -m json.tool

# Extract feed ID
FEED_ID=$(echo $CREATE_FEED_RESPONSE | python3 -c "import sys, json; d=json.load(sys.stdin); print(d.get('data', {}).get('id', ''))" 2>/dev/null)

if [ -n "$FEED_ID" ]; then
    echo -e "${GREEN}Feed created with ID: $FEED_ID${NC}"
    
    # 5. LIKE FEED
    echo -e "\n${YELLOW}[5] Like Feed${NC}"
    curl -s -X POST "$BASE_URL/feed/like/$FEED_ID/" \
      -H "Authorization: Bearer $ACCESS_TOKEN" | python3 -m json.tool
    
    # 6. ADD COMMENT
    echo -e "\n${YELLOW}[6] Add Comment to Feed${NC}"
    curl -s -X POST "$BASE_URL/feed/comment/$FEED_ID/" \
      -H "Authorization: Bearer $ACCESS_TOKEN" \
      -H "Content-Type: application/json" \
      -d '{"text": "MashaAllah, great post!"}' | python3 -m json.tool
    
    # 7. GET COMMENTS
    echo -e "\n${YELLOW}[7] Get Comments${NC}"
    curl -s -X GET "$BASE_URL/feed/comments/$FEED_ID/" \
      -H "Authorization: Bearer $ACCESS_TOKEN" | python3 -m json.tool
fi

# 8. GET FEED
echo -e "\n${YELLOW}[8] Get Feed${NC}"
curl -s -X GET "$BASE_URL/feed/" \
  -H "Authorization: Bearer $ACCESS_TOKEN" | python3 -m json.tool

# 9. SEARCH FEED
echo -e "\n${YELLOW}[9] Search Feed (query: 'test')${NC}"
curl -s -X GET "$BASE_URL/feed/search/?q=test" \
  -H "Authorization: Bearer $ACCESS_TOKEN" | python3 -m json.tool

# 10. CREATE STORY WITH IMAGE (if image exists)
echo -e "\n${YELLOW}[10] Create Story${NC}"
echo -e "${YELLOW}Note: To test story with image, create a test image first:${NC}"
echo "  echo \"test\" > /tmp/test.txt && convert -size 100x100 xc:red /tmp/test.jpg"
echo -e "${YELLOW}Or run: touch /tmp/test.jpg && curl ...${NC}"

# Check if test image exists
if [ -f "/tmp/test.jpg" ]; then
    curl -s -X POST "$BASE_URL/stories/create/" \
      -H "Authorization: Bearer $ACCESS_TOKEN" \
      -F "media=@/tmp/test.jpg" | python3 -m json.tool
else
    echo -e "${RED}Skipping - no test image found at /tmp/test.jpg${NC}"
fi

# 11. GET STORIES
echo -e "\n${YELLOW}[11] Get Stories${NC}"
curl -s -X GET "$BASE_URL/stories/" \
  -H "Authorization: Bearer $ACCESS_TOKEN" | python3 -m json.tool

# 12. FOLLOW A USER (create second user first)
echo -e "\n${YELLOW}[12] Create Second User for Follow Test${NC}"
REGISTER_RESPONSE2=$(curl -s -X POST "$BASE_URL/user/create/" \
  -H "Content-Type: application/json" \
  -d '{
    "username": "seconduser_'$(date +%s)'",
    "password": "test123",
    "nama": "Second User",
    "email": "second@example.com",
    "alamat": "Bandung",
    "telepon": "08987654321"
  }')
echo $REGISTER_RESPONSE2 | python3 -m json.tool

# Extract second user ID
SECOND_USER_ID=$(echo $REGISTER_RESPONSE2 | python3 -c "import sys, json; print(json.load(sys.stdin).get('id', ''))" 2>/dev/null)

if [ -n "$SECOND_USER_ID" ]; then
    echo -e "${GREEN}Second user created with ID: $SECOND_USER_ID${NC}"
    
    # 13. FOLLOW SECOND USER
    echo -e "\n${YELLOW}[13] Follow Second User${NC}"
    curl -s -X POST "$BASE_URL/follow/$SECOND_USER_ID/" \
      -H "Authorization: Bearer $ACCESS_TOKEN" | python3 -m json.tool
    
    # 14. CHECK FOLLOW STATUS
    echo -e "\n${YELLOW}[14] Check Follow Status${NC}"
    curl -s -X GET "$BASE_URL/follow/check/$SECOND_USER_ID/" \
      -H "Authorization: Bearer $ACCESS_TOKEN" | python3 -m json.tool
    
    # 15. GET FOLLOWING LIST
    echo -e "\n${YELLOW}[15] Get Following List${NC}"
    curl -s -X GET "$BASE_URL/following/$SECOND_USER_ID/" \
      -H "Authorization: Bearer $ACCESS_TOKEN" | python3 -m json.tool
    
    # 16. UNFOLLOW
    echo -e "\n${YELLOW}[16] Unfollow Second User${NC}"
    curl -s -X DELETE "$BASE_URL/unfollow/$SECOND_USER_ID/" \
      -H "Authorization: Bearer $ACCESS_TOKEN" | python3 -m json.tool
fi

echo -e "\n${GREEN}========================================${NC}"
echo -e "${GREEN}Testing Complete!${NC}"
echo -e "${GREEN}========================================${NC}"