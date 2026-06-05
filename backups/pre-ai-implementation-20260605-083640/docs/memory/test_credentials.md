# CineMorph AI Test Credentials

## Authentication Method
- **Auth Type**: Emergent Google OAuth
- **Login Flow**: Users authenticate via Google OAuth through Emergent Auth service

## Test Accounts
- Use any valid Google account for testing
- No password-based credentials needed (Google OAuth flow)

## Session Testing
For backend testing, create test sessions using mongosh:
```bash
mongosh --eval "
use('test_database');
var userId = 'test-user-' + Date.now();
var sessionToken = 'test_session_' + Date.now();
db.users.insertOne({
  user_id: userId,
  email: 'test.user.' + Date.now() + '@example.com',
  name: 'Test User',
  picture: 'https://via.placeholder.com/150',
  created_at: new Date()
});
db.user_sessions.insertOne({
  user_id: userId,
  session_token: sessionToken,
  expires_at: new Date(Date.now() + 7*24*60*60*1000),
  created_at: new Date()
});
print('Session token: ' + sessionToken);
print('User ID: ' + userId);
"
```

## Notes
- All users have equal access (no RBAC)
- Test session tokens expire in 7 days
- See /app/auth_testing.md for detailed testing procedures
