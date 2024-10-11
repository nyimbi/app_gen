curl -XPOST http://localhost:5000/api/v1/security/login -d \
  '{"username": "admin", "password": "abc", "provider": "db"}' \
  -H "Content-Type: application/json"
