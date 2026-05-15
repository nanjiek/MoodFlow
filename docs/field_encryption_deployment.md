# Field Encryption Deployment SOP

This note covers the production rollout requirements for encrypted emotion text fields.

## Startup guard

When `DJANGO_DEBUG=false`, the backend now fails during startup unless both of the following are true:

- `MOODFLOW_FIELD_ENCRYPTION_KEY` is configured.
- `MOODFLOW_FIELD_ENCRYPTION_ALLOW_FALLBACK` is unset or explicitly `false`.

Recommended production example:

```env
DJANGO_DEBUG=false
MOODFLOW_FIELD_ENCRYPTION_KEY=<strong-random-key>
MOODFLOW_FIELD_ENCRYPTION_ALLOW_FALLBACK=false
```

## First-time rollout steps

Use this SOP the first time field encryption is enabled in an environment that may already contain emotion records.

1. Configure `MOODFLOW_FIELD_ENCRYPTION_KEY`.
2. Confirm `MOODFLOW_FIELD_ENCRYPTION_ALLOW_FALLBACK=false`.
3. Deploy the backend code and install dependencies as usual.
4. Run database migrations.
5. Run the legacy encryption backfill command once before opening traffic:

```bash
cd backend
python manage.py encrypt_legacy_emotion_records
```

6. Verify the command output reports the number of updated records.
7. Smoke test encrypted record create/read flows in the target environment.

## Why the backfill is required

Older rows may have `is_encrypted=true` while the stored `emotion_text` is still plaintext. The backfill command rewrites only those legacy plaintext payloads into encrypted storage format and leaves already encrypted rows unchanged.
