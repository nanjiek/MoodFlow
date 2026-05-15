# API Examples

Default local addresses:

- Backend: `http://localhost:8000`
- Model service: `http://localhost:8010`

Most user-side APIs return the unified structure below:

```json
{
  "code": 0,
  "message": "success",
  "data": {}
}
```

## Requirement Alignment Notes

The current backend covers the main user contract for registration, login, password reset, social account binding, encrypted emotion record storage, reminder preference management, and personal data export.

The following requirement-related limits are important for frontend, QA, and integration teams:

- Social login is currently contract-complete but still uses mock/local identity resolution through `mock_open_id` or `open_id`. Real WeChat/QQ OAuth code exchange is not wired in yet.
- Reminder delivery supports preference storage, device token registration, manual trigger, and server-side scheduled dispatch through `python manage.py dispatch_reminders`, but it is still a polling scheduler rather than a queue-based push system.
- Firebase production delivery is not connected yet. Local and test environments rely on mock push behavior.
- Emotion export is currently synchronous. The response returns generated content directly after request completion.
- Password reset intentionally hides whether a phone number exists. Frontend should not infer account existence from the send-code response.

## Admin Login

```bash
curl -X POST http://localhost:8000/api/admin/auth/login/ \
  -H "Content-Type: application/json" \
  -d '{
    "username": "admin",
    "password": "MoodFlow@123456"
  }'
```

## User Register

`POST /api/auth/register/`

```bash
curl -X POST http://localhost:8000/api/auth/register/ \
  -H "Content-Type: application/json" \
  -d '{
    "phone": "13800138000",
    "password": "MoodFlowUser123!",
    "nickname": "Mood User"
  }'
```

Example response:

```json
{
  "code": 0,
  "message": "success",
  "data": {
    "token": "<jwt-token>",
    "token_type": "Bearer",
    "expires_at": "2026-05-15T16:00:00+08:00",
    "profile": {
      "id": 1,
      "external_id": "13800138000",
      "nickname": "Mood User",
      "avatar_url": "",
      "gender": "unknown",
      "birth_date": null,
      "phone": "13800138000",
      "email": "",
      "signature": "",
      "anonymous_mode": false,
      "emotion_encryption_enabled": false,
      "privacy": {
        "anonymous_mode": false,
        "emotion_encryption_enabled": false
      },
      "social_accounts": [],
      "created_at": "2026-05-15T12:00:00+08:00",
      "updated_at": "2026-05-15T12:00:00+08:00"
    }
  }
}
```

## User Login

`POST /api/auth/login/`

```bash
curl -X POST http://localhost:8000/api/auth/login/ \
  -H "Content-Type: application/json" \
  -d '{
    "phone": "13800138000",
    "password": "MoodFlowUser123!"
  }'
```

## User Profile

Get current user:

```bash
curl http://localhost:8000/api/me/ \
  -H "Authorization: Bearer <jwt-token>"
```

Update profile:

```bash
curl -X PATCH http://localhost:8000/api/me/ \
  -H "Authorization: Bearer <jwt-token>" \
  -H "Content-Type: application/json" \
  -d '{
    "nickname": "Updated Name",
    "email": "user@example.com",
    "signature": "Keep going."
  }'
```

Update privacy settings:

```bash
curl -X PATCH http://localhost:8000/api/me/privacy/ \
  -H "Authorization: Bearer <jwt-token>" \
  -H "Content-Type: application/json" \
  -d '{
    "anonymous_mode": true,
    "emotion_encryption_enabled": true
  }'
```

## Social Login

### 1. Request login state

`POST /api/auth/social/{provider}/state/`

Supported providers:

- `wechat`
- `qq`

```bash
curl -X POST http://localhost:8000/api/auth/social/wechat/state/
```

Example response:

```json
{
  "code": 0,
  "message": "success",
  "data": {
    "provider": "wechat",
    "state": "6hJ3R8mP...",
    "expires_at": "2026-05-15T12:10:00+08:00"
  }
}
```

### 2. Complete login

Current implementation supports mock/local identity resolution through `mock_open_id` or `open_id`.

`POST /api/auth/social/{provider}/login/`

```bash
curl -X POST http://localhost:8000/api/auth/social/wechat/login/ \
  -H "Content-Type: application/json" \
  -d '{
    "state": "<state>",
    "mock_open_id": "wx-open-001",
    "nickname": "WeChat User",
    "avatar_url": "https://example.com/avatar.png"
  }'
```

Example response:

```json
{
  "code": 0,
  "message": "success",
  "data": {
    "token": "<jwt-token>",
    "token_type": "Bearer",
    "expires_at": "2026-05-15T16:00:00+08:00",
    "profile": {
      "id": 2,
      "external_id": "wechat:wx-open-001",
      "nickname": "WeChat User",
      "avatar_url": "https://example.com/avatar.png"
    },
    "social_account": {
      "id": 1,
      "provider": "wechat",
      "open_id": "wx-open-001",
      "union_id": "",
      "app_id": "wechat-mock-app",
      "nickname": "WeChat User",
      "avatar_url": "https://example.com/avatar.png",
      "last_login_at": "2026-05-15T12:00:00+08:00",
      "created_at": "2026-05-15T12:00:00+08:00",
      "updated_at": "2026-05-15T12:00:00+08:00"
    },
    "is_first_login": true
  }
}
```

### 3. View and bind social accounts

View bindings:

```bash
curl http://localhost:8000/api/me/social-bindings/ \
  -H "Authorization: Bearer <jwt-token>"
```

Bind another account:

```bash
curl -X POST http://localhost:8000/api/me/social-bindings/ \
  -H "Authorization: Bearer <jwt-token>" \
  -H "Content-Type: application/json" \
  -d '{
    "provider": "qq",
    "state": "<state>",
    "mock_open_id": "qq-open-001",
    "nickname": "QQ User"
  }'
```

Unbind:

```bash
curl -X DELETE http://localhost:8000/api/me/social-bindings/1/ \
  -H "Authorization: Bearer <jwt-token>"
```

## Password Reset

### 1. Send code

`POST /api/auth/password-reset/send-code/`

```bash
curl -X POST http://localhost:8000/api/auth/password-reset/send-code/ \
  -H "Content-Type: application/json" \
  -d '{
    "phone": "13800138000"
  }'
```

Important behavior:

- This endpoint returns a success response even if the phone number is not registered.
- `debug_code` is returned only when `PASSWORD_RESET_EXPOSE_DEBUG_CODE=true`.
- Production should keep `PASSWORD_RESET_EXPOSE_DEBUG_CODE=false`.

Example response in local/debug-enabled testing:

```json
{
  "code": 0,
  "message": "code sent",
  "data": {
    "request_id": "5f6f4743bb2d4fbe9aa1fd1d0f1f6d43",
    "expires_at": "2026-05-15T12:05:00+08:00",
    "phone": "13800138000",
    "cooldown_seconds": 60,
    "debug_code": "246810"
  }
}
```

### 2. Verify code

`POST /api/auth/password-reset/verify-code/`

```bash
curl -X POST http://localhost:8000/api/auth/password-reset/verify-code/ \
  -H "Content-Type: application/json" \
  -d '{
    "phone": "13800138000",
    "request_id": "<request-id>",
    "code": "246810"
  }'
```

### 3. Reset password

`POST /api/auth/password-reset/reset/`

```bash
curl -X POST http://localhost:8000/api/auth/password-reset/reset/ \
  -H "Content-Type: application/json" \
  -d '{
    "phone": "13800138000",
    "request_id": "<request-id>",
    "code": "246810",
    "new_password": "NewPassword123!"
  }'
```

Security behavior:

- If the request is invalid, expired, already consumed, or tied to a non-existent user, the API returns a generic validation error instead of exposing account existence.

## Emotion Record APIs

### Create a record

`POST /api/emotions/records/`

```bash
curl -X POST http://localhost:8000/api/emotions/records/ \
  -H "Authorization: Bearer <jwt-token>" \
  -H "Content-Type: application/json" \
  -d '{
    "selected_label": "happy",
    "text": "Today felt steady and productive.",
    "is_encrypted": true,
    "recorded_at": "2026-05-15T10:00:00+08:00"
  }'
```

### List current user records

```bash
curl "http://localhost:8000/api/emotions/records/?selected_label=happy&is_encrypted=true" \
  -H "Authorization: Bearer <jwt-token>"
```

### View record analysis

`GET /api/emotions/records/{id}/analysis/`

```bash
curl http://localhost:8000/api/emotions/records/1/analysis/ \
  -H "Authorization: Bearer <jwt-token>"
```

### Correct analysis result

`POST /api/emotions/records/{id}/analysis/correct/`

```bash
curl -X POST http://localhost:8000/api/emotions/records/1/analysis/correct/ \
  -H "Authorization: Bearer <jwt-token>" \
  -H "Content-Type: application/json" \
  -d '{
    "accepted": false,
    "corrected_label": "calm",
    "note": "This felt more calm than happy."
  }'
```

### Toggle favorite

`POST /api/emotions/records/{id}/favorite/`

```bash
curl -X POST http://localhost:8000/api/emotions/records/1/favorite/ \
  -H "Authorization: Bearer <jwt-token>" \
  -H "Content-Type: application/json" \
  -d '{
    "is_collect": true
  }'
```

### Export own data

Create export:

```bash
curl -X POST http://localhost:8000/api/emotions/exports/ \
  -H "Authorization: Bearer <jwt-token>" \
  -H "Content-Type: application/json" \
  -d '{
    "file_format": "json",
    "start_at": "2026-05-15T00:00:00+08:00",
    "end_at": "2026-05-15T23:59:59+08:00"
  }'
```

Current behavior:

- Export generation is synchronous.
- Only the authenticated user's own records are included.
- Supported formats: `json`, `csv`
- Large exports currently execute in-request and are not offloaded to a background worker.

List export tasks:

```bash
curl http://localhost:8000/api/emotions/exports/ \
  -H "Authorization: Bearer <jwt-token>"
```

Download export:

```bash
curl http://localhost:8000/api/emotions/exports/1/download/ \
  -H "Authorization: Bearer <jwt-token>"
```

## Reminder APIs

### Register device token

`POST /api/emotions/devices/`

```bash
curl -X POST http://localhost:8000/api/emotions/devices/ \
  -H "Authorization: Bearer <jwt-token>" \
  -H "Content-Type: application/json" \
  -d '{
    "token": "device-token-001",
    "platform": "android",
    "device_id": "pixel-1"
  }'
```

### View device tokens

```bash
curl http://localhost:8000/api/emotions/devices/ \
  -H "Authorization: Bearer <jwt-token>"
```

### Update reminder preference

`PATCH /api/emotions/reminder-preferences/`

```bash
curl -X PATCH http://localhost:8000/api/emotions/reminder-preferences/ \
  -H "Authorization: Bearer <jwt-token>" \
  -H "Content-Type: application/json" \
  -d '{
    "enabled": true,
    "timezone": "Asia/Shanghai",
    "reminder_time": "09:00:00",
    "quiet_hours_start": "23:00:00",
    "quiet_hours_end": "07:00:00",
    "frequency_per_day": 2,
    "preferred_content_types": ["phrase"]
  }'
```

### Manual reminder trigger

`POST /api/emotions/reminders/trigger/`

```bash
curl -X POST http://localhost:8000/api/emotions/reminders/trigger/ \
  -H "Authorization: Bearer <jwt-token>"
```

Current behavior:

- This endpoint triggers reminders for the current user immediately.
- Background scheduled dispatch is handled separately by the server-side command `python manage.py dispatch_reminders`.
- Real Firebase delivery still requires production provider integration; mock mode is available for local testing.
- `frequency_per_day` is currently enforced as a minimum dispatch interval, not as exact wall-clock delivery slots.

## Reports

Daily report:

```bash
curl "http://localhost:8000/api/emotions/reports/daily/?date=2026-05-15" \
  -H "Authorization: Bearer <jwt-token>"
```

Weekly report:

```bash
curl "http://localhost:8000/api/emotions/reports/weekly/?start_date=2026-05-09&end_date=2026-05-15" \
  -H "Authorization: Bearer <jwt-token>"
```

Growth curve:

```bash
curl "http://localhost:8000/api/emotions/growth-curve/?days=7" \
  -H "Authorization: Bearer <jwt-token>"
```

## Model Service

Predict emotion:

```bash
curl -X POST http://localhost:8010/predict/emotion \
  -H "Content-Type: application/json" \
  -d '{
    "text": "Today I feel a bit stressed and tense.",
    "selected_label": "anxious",
    "user_id": "demo-user-001"
  }'
```

Trend analysis:

```bash
curl -X POST http://localhost:8010/analyze/trend \
  -H "Content-Type: application/json" \
  -d '{
    "records": [
      {"label": "anxious"},
      {"label": "anxious"},
      {"label": "sad"},
      {"predicted_label": "tired"}
    ]
  }'
```

## Error Response Examples

Most validation and business errors currently use the unified structure below:

```json
{
  "code": "invalid",
  "message": "validation error",
  "data": {}
}
```

Notes:

- `code` comes from the exception type and may vary, but validation failures commonly return `invalid` or `validation_error`.
- If the backend raises a DRF validation error with field-level details, `message` is usually `validation error` and the actual reason is placed in `data`.
- If the backend raises a validation error with top-level `detail`, the message may be promoted directly to `message`.

### Password reset: invalid or expired request

Typical triggers:

- `request_id` does not exist
- code has expired
- code has already been consumed
- request belongs to a non-existent phone account

Example response:

```json
{
  "code": "validation_error",
  "message": "validation error",
  "data": {
    "detail": [
      "Invalid or expired password reset request."
    ]
  }
}
```

### Password reset: wrong verification code

Example response:

```json
{
  "code": "validation_error",
  "message": "validation error",
  "data": {
    "code": [
      "Invalid verification code."
    ]
  }
}
```

### Password reset: send too frequently

Example response:

```json
{
  "code": "validation_error",
  "message": "validation error",
  "data": {
    "phone": [
      "Verification code sent too frequently. Please try again later."
    ]
  }
}
```

### Social binding conflict

Scenario:

- The same WeChat or QQ account is already bound to another MoodFlow user.

Example response:

```json
{
  "code": "validation_error",
  "message": "validation error",
  "data": {
    "open_id": [
      "This social account is already linked to another user."
    ]
  }
}
```

### Social login or binding: invalid state

Scenario:

- missing `state`
- expired `state`
- reused `state`

Example response:

```json
{
  "code": "validation_error",
  "message": "validation error",
  "data": {
    "state": [
      "Invalid or expired social login state."
    ]
  }
}
```

### Export download: task not ready

Scenario:

- The export task exists, but its status is not yet `completed`.

Example response:

```json
{
  "code": "validation_error",
  "message": "validation error",
  "data": {
    "task_id": [
      "Export task is not ready."
    ]
  }
}
```

### Export download: task not found or not owned by current user

Scenario:

- The task id does not exist
- The task belongs to another user

Current behavior:

- This case returns HTTP `404`.
- The exact body depends on the framework-level `Http404` handling path, so frontend should primarily rely on the HTTP status code for this case.

### Reminder trigger: no active device token

Scenario:

- The user has not registered any active device token.

Current behavior:

- This is not treated as an error.
- The API returns success with an empty list.

Example response:

```json
{
  "code": 0,
  "message": "triggered",
  "data": []
}
```

### Reminder trigger: reminders disabled

Scenario:

- The user has `enabled=false` in reminder preferences.

Current behavior:

- This is also treated as a successful no-op.

Example response:

```json
{
  "code": 0,
  "message": "triggered",
  "data": []
}
```
