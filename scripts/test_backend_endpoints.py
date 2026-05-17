from __future__ import annotations

import json
import subprocess
import sys
import time
from dataclasses import asdict, dataclass
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any
from urllib.parse import quote

import requests


ROOT = Path(__file__).resolve().parents[1]
BACKEND_URL = "http://localhost:8000"
MODEL_URL = "http://localhost:8010"
REPORT_JSON = ROOT / "docs" / "backend_api_test_record.json"
REPORT_MD = ROOT / "docs" / "backend_api_test_record.md"
TIMEOUT = 20


@dataclass
class EndpointResult:
    name: str
    method: str
    url: str
    status_code: int | None
    ok: bool
    expected_status: list[int]
    duration_ms: int
    note: str
    response_preview: str


class TestFailure(RuntimeError):
    pass


class EndpointTester:
    def __init__(self) -> None:
        self.results: list[EndpointResult] = []
        self.admin = requests.Session()
        self.user = requests.Session()
        self.social_user = requests.Session()
        self.context: dict[str, Any] = {
            "started_at": datetime.now(timezone.utc).isoformat(),
        }

    def run(self) -> int:
        try:
            self._bootstrap()
            self._test_public_accounts()
            self._test_user_emotions()
            self._test_user_companion()
            self._test_admin_accounts()
            self._test_admin_emotions()
            self._test_admin_content()
            self._test_admin_moderation()
            self._test_admin_analytics()
            self._test_admin_mlops()
            self._test_model_service()
        finally:
            self.context["finished_at"] = datetime.now(timezone.utc).isoformat()
            self._write_reports()

        failures = [result for result in self.results if not result.ok]
        return 1 if failures else 0

    def _bootstrap(self) -> None:
        self._compose_check()
        self._ensure_mlops_samples()
        self._call("Backend health", "GET", f"{BACKEND_URL}/api/health/", expected_status=[200], required=True)
        self._call("Model health", "GET", f"{MODEL_URL}/health", expected_status=[200], required=True)
        self._admin_login(required=True)
        self._register_user(required=True)

    def _compose_check(self) -> None:
        cmd = ["docker", "compose", "ps", "--status", "running"]
        proc = subprocess.run(
            cmd,
            cwd=ROOT,
            capture_output=True,
            text=True,
            encoding="utf-8",
            errors="replace",
            check=False,
        )
        if proc.returncode != 0:
            raise TestFailure(f"docker compose is not ready: {proc.stderr.strip() or proc.stdout.strip()}")
        self.context["compose_ps"] = proc.stdout.strip()

    def _docker_backend_shell(self, code: str) -> str:
        cmd = [
            "docker",
            "compose",
            "exec",
            "-T",
            "backend",
            "python",
            "manage.py",
            "shell",
            "-c",
            code,
        ]
        proc = subprocess.run(
            cmd,
            cwd=ROOT,
            capture_output=True,
            text=True,
            encoding="utf-8",
            errors="replace",
            check=False,
        )
        if proc.returncode != 0:
            raise TestFailure(proc.stderr.strip() or proc.stdout.strip() or "docker backend shell failed")
        return proc.stdout.strip()

    def _ensure_mlops_samples(self) -> None:
        unique = datetime.now(timezone.utc).strftime("%Y%m%d%H%M%S")
        code = f"""
from mlops.models import TrainingSample
sample_one = TrainingSample.objects.create(
    text="api smoke sample {unique} A",
    raw_label="happy",
    mapped_label="happy",
    source="api_smoke",
)
sample_two = TrainingSample.objects.create(
    text="api smoke sample {unique} B",
    raw_label="sad",
    mapped_label="sad",
    source="api_smoke",
)
print(f"{{sample_one.id}},{{sample_two.id}}")
"""
        raw_ids = self._docker_backend_shell(code)
        lines = [line.strip() for line in raw_ids.splitlines() if line.strip()]
        id_line = lines[-1]
        first_id, second_id = [int(item) for item in id_line.split(",")]
        self.context["training_sample_ids"] = [first_id, second_id]

    def _call(
        self,
        name: str,
        method: str,
        url: str,
        *,
        session: requests.Session | None = None,
        expected_status: list[int] | None = None,
        json_body: Any | None = None,
        params: dict[str, Any] | None = None,
        required: bool = False,
        note: str = "",
    ) -> requests.Response:
        active_session = session or requests.Session()
        expected = expected_status or [200]
        started = time.perf_counter()
        response: requests.Response | None = None
        preview = ""
        ok = False
        status_code: int | None = None
        failure_message = ""
        try:
            response = active_session.request(
                method=method,
                url=url,
                json=json_body,
                params=params,
                timeout=TIMEOUT,
            )
            status_code = response.status_code
            preview = self._response_preview(response)
            ok = response.status_code in expected
            if not ok:
                failure_message = f"expected {expected}, got {response.status_code}"
        except Exception as exc:  # noqa: BLE001
            failure_message = str(exc)
            preview = str(exc)
        duration_ms = int((time.perf_counter() - started) * 1000)
        final_note = note if ok else f"{note} {failure_message}".strip()
        self.results.append(
            EndpointResult(
                name=name,
                method=method,
                url=self._full_url_with_params(url, params),
                status_code=status_code,
                ok=ok,
                expected_status=expected,
                duration_ms=duration_ms,
                note=final_note,
                response_preview=preview,
            )
        )
        if required and not ok:
            raise TestFailure(f"{name} failed: {failure_message}")
        if response is None:
            raise TestFailure(f"{name} did not return a response")
        return response

    def _full_url_with_params(self, url: str, params: dict[str, Any] | None) -> str:
        if not params:
            return url
        prepared = requests.Request("GET", url, params=params).prepare()
        return prepared.url

    def _response_preview(self, response: requests.Response) -> str:
        try:
            payload = response.json()
            serialized = json.dumps(payload, ensure_ascii=True, sort_keys=True)
        except ValueError:
            serialized = response.text
        serialized = serialized.replace("\n", " ").strip()
        return serialized[:320]

    def _json(self, response: requests.Response) -> Any:
        return response.json()

    def _payload_data(self, payload: Any) -> Any:
        if isinstance(payload, dict) and "data" in payload:
            return payload["data"]
        return payload

    def _result_items(self, payload: Any) -> list[Any]:
        data = self._payload_data(payload)
        if isinstance(data, dict) and "results" in data:
            return list(data["results"])
        if isinstance(data, list):
            return data
        raise TestFailure(f"Unable to extract results from payload: {json.dumps(payload, ensure_ascii=True)[:200]}")

    def _admin_login(self, *, required: bool = False) -> None:
        response = self._call(
            "Admin login",
            "POST",
            f"{BACKEND_URL}/api/admin/auth/login/",
            expected_status=[200],
            json_body={"username": "admin", "password": "MoodFlow@123456"},
            required=required,
        )
        payload = self._json(response)
        token = payload["token"]
        self.admin.headers["Authorization"] = f"Bearer {token}"
        self.context["admin_profile"] = payload.get("profile", {})

    def _register_user(self, *, required: bool = False) -> None:
        stamp = datetime.now(timezone.utc).strftime("%m%d%H%M%S")
        phone = f"139{stamp}"[:11]
        password = "MoodFlowUser123!"
        nickname = f"api-user-{stamp}"
        response = self._call(
            "User register",
            "POST",
            f"{BACKEND_URL}/api/auth/register/",
            expected_status=[201],
            json_body={"phone": phone, "password": password, "nickname": nickname},
            required=required,
        )
        payload = self._json(response)["data"]
        self.user.headers["Authorization"] = f"Bearer {payload['token']}"
        self.context["user_phone"] = phone
        self.context["user_password"] = password
        self.context["user_id"] = payload["profile"]["id"]
        self.context["user_profile"] = payload["profile"]

    def _patch_password_reset_code(self, request_id: str, code: str) -> None:
        shell = f"""
from datetime import timedelta
from django.utils import timezone
from accounts.models import PhoneVerificationCode
from accounts.services import _hash_verification_code
obj = PhoneVerificationCode.objects.get(request_id={json.dumps(request_id)})
obj.code_hash = _hash_verification_code({json.dumps(code)})
obj.attempt_count = 0
obj.max_attempts = 5
obj.verified_at = None
obj.consumed_at = None
obj.expires_at = timezone.now() + timedelta(minutes=10)
obj.save(update_fields=["code_hash", "attempt_count", "max_attempts", "verified_at", "consumed_at", "expires_at", "updated_at"])
print("ok")
"""
        self._docker_backend_shell(shell)

    def _test_public_accounts(self) -> None:
        phone = self.context["user_phone"]
        password = self.context["user_password"]
        self._call(
            "User login",
            "POST",
            f"{BACKEND_URL}/api/auth/login/",
            expected_status=[200],
            json_body={"phone": phone, "password": password},
        )
        self._call("User profile get", "GET", f"{BACKEND_URL}/api/me/", session=self.user, expected_status=[200])
        self._call(
            "User profile patch",
            "PATCH",
            f"{BACKEND_URL}/api/me/",
            session=self.user,
            expected_status=[200],
            json_body={
                "nickname": "API Smoke User",
                "email": "api-smoke@example.com",
                "signature": "Testing backend endpoints.",
            },
        )
        self._call("User privacy get", "GET", f"{BACKEND_URL}/api/me/privacy/", session=self.user, expected_status=[200])
        self._call(
            "User privacy patch",
            "PATCH",
            f"{BACKEND_URL}/api/me/privacy/",
            session=self.user,
            expected_status=[200],
            json_body={"anonymous_mode": True, "emotion_encryption_enabled": True},
        )
        self._call("Social state wechat", "POST", f"{BACKEND_URL}/api/auth/social/wechat/state/", expected_status=[200])
        social_state_response = self._call(
            "Social state qq",
            "POST",
            f"{BACKEND_URL}/api/auth/social/qq/state/",
            expected_status=[200],
        )
        social_state = self._json(social_state_response)["data"]["state"]
        social_login_response = self._call(
            "Social login wechat",
            "POST",
            f"{BACKEND_URL}/api/auth/social/wechat/login/",
            expected_status=[200],
            json_body={
                "state": self._json(
                    self._call(
                        "Social state wechat second",
                        "POST",
                        f"{BACKEND_URL}/api/auth/social/wechat/state/",
                        expected_status=[200],
                    )
                )["data"]["state"],
                "mock_open_id": f"wx-api-{int(time.time())}",
                "nickname": "API WeChat User",
                "avatar_url": "https://example.com/avatar.png",
            },
        )
        social_payload = self._json(social_login_response)["data"]
        self.social_user.headers["Authorization"] = f"Bearer {social_payload['token']}"
        self.context["social_user_id"] = social_payload["profile"]["id"]
        self._call("User social bindings get", "GET", f"{BACKEND_URL}/api/me/social-bindings/", session=self.user, expected_status=[200])
        bind_response = self._call(
            "User social bind qq",
            "POST",
            f"{BACKEND_URL}/api/me/social-bindings/",
            session=self.user,
            expected_status=[200],
            json_body={
                "provider": "qq",
                "state": social_state,
                "mock_open_id": f"qq-api-{int(time.time())}",
                "nickname": "API QQ User",
            },
        )
        binding_id = self._json(bind_response)["data"]["id"]
        self._call(
            "User social unbind",
            "DELETE",
            f"{BACKEND_URL}/api/me/social-bindings/{binding_id}/",
            session=self.user,
            expected_status=[200],
        )

        send_code_response = self._call(
            "Password reset send code",
            "POST",
            f"{BACKEND_URL}/api/auth/password-reset/send-code/",
            expected_status=[200],
            json_body={"phone": phone},
        )
        request_id = self._json(send_code_response)["data"]["request_id"]
        known_code = "246810"
        self._patch_password_reset_code(request_id, known_code)
        self._call(
            "Password reset verify code",
            "POST",
            f"{BACKEND_URL}/api/auth/password-reset/verify-code/",
            expected_status=[200],
            json_body={"phone": phone, "request_id": request_id, "code": known_code},
        )
        new_password = "MoodFlowUser456!"
        self._call(
            "Password reset apply",
            "POST",
            f"{BACKEND_URL}/api/auth/password-reset/reset/",
            expected_status=[200],
            json_body={"phone": phone, "request_id": request_id, "code": known_code, "new_password": new_password},
        )
        self.context["user_password"] = new_password
        self._call(
            "User login after reset",
            "POST",
            f"{BACKEND_URL}/api/auth/login/",
            expected_status=[200],
            json_body={"phone": phone, "password": new_password},
        )

    def _test_user_emotions(self) -> None:
        current_day = datetime.now().astimezone().date().isoformat()
        record_time = datetime.now().astimezone().replace(microsecond=0).isoformat()
        create_response = self._call(
            "User record create",
            "POST",
            f"{BACKEND_URL}/api/emotions/records/",
            session=self.user,
            expected_status=[201],
            json_body={
                "selected_label": "happy",
                "text": "API smoke test record.",
                "emoji_id": "smile-api",
                "is_collect": False,
                "is_encrypted": True,
                "recorded_at": record_time,
            },
        )
        record_payload = self._json(create_response)["data"]
        record_id = record_payload["id"]
        analysis_id = record_payload["analysis"]["id"]
        self.context["record_id"] = record_id
        self.context["analysis_id"] = analysis_id

        self._call(
            "User records list",
            "GET",
            f"{BACKEND_URL}/api/emotions/records/",
            session=self.user,
            expected_status=[200],
            params={"selected_label": "happy", "is_encrypted": True},
        )
        self._call(
            "User record retrieve",
            "GET",
            f"{BACKEND_URL}/api/emotions/records/{record_id}/",
            session=self.user,
            expected_status=[200],
        )
        self._call(
            "User record update",
            "PATCH",
            f"{BACKEND_URL}/api/emotions/records/{record_id}/",
            session=self.user,
            expected_status=[200],
            json_body={
                "selected_label": "calm",
                "text": "API smoke test record updated.",
                "emoji_id": "calm-api",
                "is_collect": False,
                "is_encrypted": True,
                "recorded_at": record_time,
            },
        )
        self._call(
            "User record favorite",
            "POST",
            f"{BACKEND_URL}/api/emotions/records/{record_id}/favorite/",
            session=self.user,
            expected_status=[200],
            json_body={"is_collect": True},
        )
        self._call(
            "User record toggle collect",
            "POST",
            f"{BACKEND_URL}/api/emotions/records/{record_id}/toggle-collect/",
            session=self.user,
            expected_status=[200],
        )
        self._call(
            "User record analysis",
            "GET",
            f"{BACKEND_URL}/api/emotions/records/{record_id}/analysis/",
            session=self.user,
            expected_status=[200],
        )
        self._call(
            "User record analysis correct",
            "POST",
            f"{BACKEND_URL}/api/emotions/records/{record_id}/analysis/correct/",
            session=self.user,
            expected_status=[200],
            json_body={"accepted": False, "corrected_label": "calm", "note": "Closer to calm."},
        )
        self._call(
            "User analysis correct by analysis id",
            "POST",
            f"{BACKEND_URL}/api/emotions/analyses/{analysis_id}/correct/",
            session=self.user,
            expected_status=[200],
            json_body={"accepted": True, "note": "Follow-up accepted."},
        )
        self._call(
            "User history by day",
            "GET",
            f"{BACKEND_URL}/api/emotions/records/history-by-day/",
            session=self.user,
            expected_status=[200],
            params={"date": current_day},
        )
        self._call(
            "User daily report",
            "GET",
            f"{BACKEND_URL}/api/emotions/reports/daily/",
            session=self.user,
            expected_status=[200],
            params={"date": current_day},
        )
        self._call(
            "User weekly report",
            "GET",
            f"{BACKEND_URL}/api/emotions/reports/weekly/",
            session=self.user,
            expected_status=[200],
            params={"start_date": current_day, "end_date": current_day},
        )
        self._call(
            "User growth curve",
            "GET",
            f"{BACKEND_URL}/api/emotions/growth-curve/",
            session=self.user,
            expected_status=[200],
            params={"days": 7, "date": current_day},
        )
        self._call("User devices get", "GET", f"{BACKEND_URL}/api/emotions/devices/", session=self.user, expected_status=[200])
        self._call(
            "User device register",
            "POST",
            f"{BACKEND_URL}/api/emotions/devices/",
            session=self.user,
            expected_status=[200],
            json_body={
                "token": f"api-device-{int(time.time())}",
                "platform": "android",
                "device_id": "api-smoke-device",
            },
        )
        self._call(
            "User reminder preference get",
            "GET",
            f"{BACKEND_URL}/api/emotions/reminder-preferences/",
            session=self.user,
            expected_status=[200],
        )
        self._call(
            "User reminder preference patch",
            "PATCH",
            f"{BACKEND_URL}/api/emotions/reminder-preferences/",
            session=self.user,
            expected_status=[200],
            json_body={
                "enabled": True,
                "timezone": "Asia/Shanghai",
                "reminder_time": "09:00:00",
                "quiet_hours_start": "23:00:00",
                "quiet_hours_end": "07:00:00",
                "frequency_per_day": 1,
                "preferred_content_types": ["phrase", "article"],
            },
        )
        self._call(
            "User reminder trigger",
            "POST",
            f"{BACKEND_URL}/api/emotions/reminders/trigger/",
            session=self.user,
            expected_status=[200],
        )
        export_response = self._call(
            "User export create",
            "POST",
            f"{BACKEND_URL}/api/emotions/exports/",
            session=self.user,
            expected_status=[201],
            json_body={
                "file_format": "json",
                "start_at": (datetime.now().astimezone() - timedelta(days=1)).replace(microsecond=0).isoformat(),
                "end_at": (datetime.now().astimezone() + timedelta(days=1)).replace(microsecond=0).isoformat(),
            },
        )
        export_id = self._json(export_response)["data"]["id"]
        self._call("User exports list", "GET", f"{BACKEND_URL}/api/emotions/exports/", session=self.user, expected_status=[200])
        self._call(
            "User export download",
            "GET",
            f"{BACKEND_URL}/api/emotions/exports/{export_id}/download/",
            session=self.user,
            expected_status=[200],
        )
        self._call(
            "User logout",
            "POST",
            f"{BACKEND_URL}/api/auth/logout/",
            session=self.user,
            expected_status=[200],
        )

    def _test_user_companion(self) -> None:
        record_id = self.context["record_id"]
        analysis_id = self.context["analysis_id"]
        self._call(
            "Companion recommendations",
            "GET",
            f"{BACKEND_URL}/api/companion/recommendations/",
            session=self.user,
            expected_status=[200],
            params={"record_id": record_id, "analysis_id": analysis_id, "limit": 3, "refresh": True},
        )

    def _test_admin_accounts(self) -> None:
        self._call("Admin profile", "GET", f"{BACKEND_URL}/api/admin/auth/profile/", session=self.admin, expected_status=[200])
        admin_user_phone = f"188{datetime.now(timezone.utc).strftime('%m%d%H%M')}"[:11]
        create_response = self._call(
            "Admin users create",
            "POST",
            f"{BACKEND_URL}/api/admin/emotions/users/",
            session=self.admin,
            expected_status=[201],
            json_body={
                "nickname": "Admin Created User",
                "external_id": f"admin-created-{int(time.time())}",
                "phone": admin_user_phone,
                "email": "admin-created@example.com",
                "signature": "Created from API smoke test.",
                "anonymous_mode": False,
                "emotion_encryption_enabled": False,
                "is_active": True,
            },
        )
        created_user_id = self._json(create_response)["id"]
        self.context["admin_created_user_id"] = created_user_id
        self._call("Admin users list", "GET", f"{BACKEND_URL}/api/admin/emotions/users/", session=self.admin, expected_status=[200])
        self._call(
            "Admin users retrieve",
            "GET",
            f"{BACKEND_URL}/api/admin/emotions/users/{created_user_id}/",
            session=self.admin,
            expected_status=[200],
        )
        self._call(
            "Admin users patch",
            "PATCH",
            f"{BACKEND_URL}/api/admin/emotions/users/{created_user_id}/",
            session=self.admin,
            expected_status=[200],
            json_body={"nickname": "Admin Updated User", "signature": "Updated during smoke test."},
        )
        self._call(
            "Admin users disable",
            "POST",
            f"{BACKEND_URL}/api/admin/emotions/users/{created_user_id}/disable/",
            session=self.admin,
            expected_status=[200],
        )
        self._call(
            "Admin users enable",
            "POST",
            f"{BACKEND_URL}/api/admin/emotions/users/{created_user_id}/enable/",
            session=self.admin,
            expected_status=[200],
        )

    def _test_admin_emotions(self) -> None:
        record_id = self.context["record_id"]
        analysis_id = self.context["analysis_id"]
        tag_response = self._call(
            "Admin tags create",
            "POST",
            f"{BACKEND_URL}/api/admin/emotions/tags/",
            session=self.admin,
            expected_status=[201],
            json_body={
                "code": f"api_tag_{int(time.time())}",
                "name": "API Test Tag",
                "description": "Created by endpoint smoke test.",
                "is_active": True,
                "sort_order": 99,
            },
        )
        tag_id = self._json(tag_response)["id"]
        self.context["admin_tag_id"] = tag_id
        self._call("Admin tags list", "GET", f"{BACKEND_URL}/api/admin/emotions/tags/", session=self.admin, expected_status=[200])
        self._call(
            "Admin tags retrieve",
            "GET",
            f"{BACKEND_URL}/api/admin/emotions/tags/{tag_id}/",
            session=self.admin,
            expected_status=[200],
        )
        self._call(
            "Admin tags patch",
            "PATCH",
            f"{BACKEND_URL}/api/admin/emotions/tags/{tag_id}/",
            session=self.admin,
            expected_status=[200],
            json_body={"description": "Patched by endpoint smoke test."},
        )
        self._call(
            "Admin tags disable",
            "POST",
            f"{BACKEND_URL}/api/admin/emotions/tags/{tag_id}/disable/",
            session=self.admin,
            expected_status=[200],
        )
        self._call(
            "Admin tags enable",
            "POST",
            f"{BACKEND_URL}/api/admin/emotions/tags/{tag_id}/enable/",
            session=self.admin,
            expected_status=[200],
        )
        self._call(
            "Admin records list",
            "GET",
            f"{BACKEND_URL}/api/admin/emotions/records/",
            session=self.admin,
            expected_status=[200],
            params={"user_id": self.context["user_id"]},
        )
        self._call(
            "Admin records retrieve",
            "GET",
            f"{BACKEND_URL}/api/admin/emotions/records/{record_id}/",
            session=self.admin,
            expected_status=[200],
        )
        self._call(
            "Admin record guide",
            "GET",
            f"{BACKEND_URL}/api/admin/emotions/records/guide/",
            session=self.admin,
            expected_status=[200],
        )
        self._call(
            "Admin record weekly summary",
            "GET",
            f"{BACKEND_URL}/api/admin/emotions/records/weekly-summary/",
            session=self.admin,
            expected_status=[200],
            params={"limit": 7},
        )
        self._call(
            "Admin record analysis by record",
            "GET",
            f"{BACKEND_URL}/api/admin/emotions/records/{record_id}/analysis/",
            session=self.admin,
            expected_status=[200],
        )
        self._call("Admin analyses list", "GET", f"{BACKEND_URL}/api/admin/emotions/analyses/", session=self.admin, expected_status=[200])
        self._call(
            "Admin analyses retrieve",
            "GET",
            f"{BACKEND_URL}/api/admin/emotions/analyses/{analysis_id}/",
            session=self.admin,
            expected_status=[200],
        )
        self._call(
            "Admin analyses correct",
            "POST",
            f"{BACKEND_URL}/api/admin/emotions/analyses/{analysis_id}/correct/",
            session=self.admin,
            expected_status=[200],
            json_body={"accepted": False, "corrected_label": "happy", "note": "Admin review pass."},
        )

    def _test_admin_content(self) -> None:
        tag_id = self.context["admin_tag_id"]
        content_response = self._call(
            "Admin companion content create",
            "POST",
            f"{BACKEND_URL}/api/admin/content/companion-contents/",
            session=self.admin,
            expected_status=[201],
            json_body={
                "content_type": "phrase",
                "emotion_tag": tag_id,
                "title": "API Test Companion Content",
                "body": "A calm, supportive phrase for API verification.",
                "resource_url": "",
                "weight": 3,
                "is_active": True,
            },
        )
        content_id = self._json(content_response)["id"]
        self.context["content_id"] = content_id
        self._call("Admin companion content list", "GET", f"{BACKEND_URL}/api/admin/content/companion-contents/", session=self.admin, expected_status=[200])
        self._call(
            "Admin companion content retrieve",
            "GET",
            f"{BACKEND_URL}/api/admin/content/companion-contents/{content_id}/",
            session=self.admin,
            expected_status=[200],
        )
        self._call(
            "Admin companion content patch",
            "PATCH",
            f"{BACKEND_URL}/api/admin/content/companion-contents/{content_id}/",
            session=self.admin,
            expected_status=[200],
            json_body={"body": "Updated companion text from API smoke test."},
        )
        config_list_response = self._call(
            "Admin system configs list",
            "GET",
            f"{BACKEND_URL}/api/admin/content/system-configs/",
            session=self.admin,
            expected_status=[200],
        )
        first_config = self._result_items(self._json(config_list_response))[0]
        config_key = first_config["key"]
        self.context["system_config_key"] = config_key
        self._call(
            "Admin system config retrieve",
            "GET",
            f"{BACKEND_URL}/api/admin/content/system-configs/{quote(config_key, safe='')}/",
            session=self.admin,
            expected_status=[200],
        )
        self._call(
            "Admin system config patch",
            "PATCH",
            f"{BACKEND_URL}/api/admin/content/system-configs/{quote(config_key, safe='')}/",
            session=self.admin,
            expected_status=[200],
            json_body={"description": "Touched by endpoint smoke test."},
        )

    def _test_admin_moderation(self) -> None:
        list_response = self._call(
            "Admin tree hole list",
            "GET",
            f"{BACKEND_URL}/api/admin/tree-hole/posts/",
            session=self.admin,
            expected_status=[200],
        )
        first_post = self._result_items(self._json(list_response))[0]
        post_id = first_post["id"]
        self.context["tree_hole_post_id"] = post_id
        self._call(
            "Admin tree hole detail",
            "GET",
            f"{BACKEND_URL}/api/admin/tree-hole/posts/{post_id}/",
            session=self.admin,
            expected_status=[200],
        )
        self._call(
            "Admin tree hole reject",
            "POST",
            f"{BACKEND_URL}/api/admin/tree-hole/posts/{post_id}/reject/",
            session=self.admin,
            expected_status=[200],
            json_body={"reason": "Rejected during API smoke test."},
        )
        self._call(
            "Admin tree hole approve",
            "POST",
            f"{BACKEND_URL}/api/admin/tree-hole/posts/{post_id}/approve/",
            session=self.admin,
            expected_status=[200],
        )

    def _test_admin_analytics(self) -> None:
        self._call("Admin analytics overview", "GET", f"{BACKEND_URL}/api/admin/statistics/overview/", session=self.admin, expected_status=[200])
        self._call(
            "Admin analytics active users",
            "GET",
            f"{BACKEND_URL}/api/admin/statistics/active-users/",
            session=self.admin,
            expected_status=[200],
            params={"days": 30},
        )
        self._call(
            "Admin analytics emotion distribution",
            "GET",
            f"{BACKEND_URL}/api/admin/statistics/emotion-distribution/",
            session=self.admin,
            expected_status=[200],
            params={"days": 30},
        )
        self._call(
            "Admin analytics feature usage",
            "GET",
            f"{BACKEND_URL}/api/admin/statistics/feature-usage/",
            session=self.admin,
            expected_status=[200],
            params={"days": 30},
        )
        self._call(
            "Admin analytics operation logs",
            "GET",
            f"{BACKEND_URL}/api/admin/statistics/operation-logs/",
            session=self.admin,
            expected_status=[200],
        )

    def _test_admin_mlops(self) -> None:
        sample_ids = self.context["training_sample_ids"]
        self._call(
            "Admin mlops samples list",
            "GET",
            f"{BACKEND_URL}/api/admin/mlops/samples/",
            session=self.admin,
            expected_status=[200],
            params={"source": "api_smoke"},
        )
        self._call(
            "Admin mlops sample retrieve",
            "GET",
            f"{BACKEND_URL}/api/admin/mlops/samples/{sample_ids[0]}/",
            session=self.admin,
            expected_status=[200],
        )
        self._call(
            "Admin mlops sample correct",
            "POST",
            f"{BACKEND_URL}/api/admin/mlops/samples/{sample_ids[0]}/correct/",
            session=self.admin,
            expected_status=[200],
            json_body={"corrected_label": "calm", "reviewer": "api-smoke"},
        )
        self._call(
            "Admin mlops sample ignore",
            "POST",
            f"{BACKEND_URL}/api/admin/mlops/samples/{sample_ids[1]}/ignore/",
            session=self.admin,
            expected_status=[200],
            json_body={"reviewer": "api-smoke"},
        )
        versions_response = self._call(
            "Admin mlops model versions list",
            "GET",
            f"{BACKEND_URL}/api/admin/mlops/model-versions/",
            session=self.admin,
            expected_status=[200],
        )
        first_version = self._result_items(self._json(versions_response))[0]
        version_id = first_version["id"]
        self.context["model_version_id"] = version_id
        self._call(
            "Admin mlops model version retrieve",
            "GET",
            f"{BACKEND_URL}/api/admin/mlops/model-versions/{version_id}/",
            session=self.admin,
            expected_status=[200],
        )
        self._call(
            "Admin mlops model version activate",
            "POST",
            f"{BACKEND_URL}/api/admin/mlops/model-versions/{version_id}/activate/",
            session=self.admin,
            expected_status=[200],
        )
        logs_response = self._call(
            "Admin mlops inference logs list",
            "GET",
            f"{BACKEND_URL}/api/admin/mlops/inference-logs/",
            session=self.admin,
            expected_status=[200],
        )
        first_log = self._result_items(self._json(logs_response))[0]
        log_id = first_log["id"]
        self._call(
            "Admin mlops inference log retrieve",
            "GET",
            f"{BACKEND_URL}/api/admin/mlops/inference-logs/{log_id}/",
            session=self.admin,
            expected_status=[200],
        )
        self._call(
            "Admin mlops status",
            "GET",
            f"{BACKEND_URL}/api/admin/mlops/status/",
            session=self.admin,
            expected_status=[200],
        )
        self._call(
            "Admin logout",
            "POST",
            f"{BACKEND_URL}/api/admin/auth/logout/",
            session=self.admin,
            expected_status=[200],
        )

    def _test_model_service(self) -> None:
        self._call(
            "Model predict emotion",
            "POST",
            f"{MODEL_URL}/predict/emotion",
            expected_status=[200],
            json_body={"text": "I feel a little tense today.", "selected_label": "anxious"},
        )
        self._call(
            "Model extract keywords",
            "POST",
            f"{MODEL_URL}/extract/keywords",
            expected_status=[200],
            json_body={"text": "I feel a little tense today and need a break.", "top_k": 5},
        )
        self._call(
            "Model analyze trend",
            "POST",
            f"{MODEL_URL}/analyze/trend",
            expected_status=[200],
            json_body={"records": [{"label": "anxious"}, {"label": "sad"}, {"predicted_label": "tired"}]},
        )

    def _write_reports(self) -> None:
        REPORT_JSON.parent.mkdir(parents=True, exist_ok=True)
        payload = {
            "summary": self._summary(),
            "context": self.context,
            "results": [asdict(item) for item in self.results],
        }
        REPORT_JSON.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
        REPORT_MD.write_text(self._markdown_report(payload), encoding="utf-8")

    def _summary(self) -> dict[str, Any]:
        total = len(self.results)
        passed = sum(1 for item in self.results if item.ok)
        failed = total - passed
        return {
            "total": total,
            "passed": passed,
            "failed": failed,
            "generated_at": datetime.now(timezone.utc).isoformat(),
        }

    def _markdown_report(self, payload: dict[str, Any]) -> str:
        summary = payload["summary"]
        lines = [
            "# Backend API Test Record",
            "",
            f"- Generated at: `{summary['generated_at']}`",
            f"- Total endpoints checked: `{summary['total']}`",
            f"- Passed: `{summary['passed']}`",
            f"- Failed: `{summary['failed']}`",
            "",
            "## Environment",
            "",
            f"- Backend URL: `{BACKEND_URL}`",
            f"- Model URL: `{MODEL_URL}`",
            "",
            "## Results",
            "",
            "| Result | Method | Endpoint | Status | Note |",
            "| --- | --- | --- | --- | --- |",
        ]
        for result in self.results:
            marker = "PASS" if result.ok else "FAIL"
            status = result.status_code if result.status_code is not None else "ERR"
            note = (result.note or "").replace("|", "/")
            endpoint = result.url.replace("|", "%7C")
            lines.append(f"| {marker} | `{result.method}` | `{endpoint}` | `{status}` | {note} |")

        failures = [item for item in self.results if not item.ok]
        lines.extend(["", "## Failures", ""])
        if not failures:
            lines.append("No failures.")
        else:
            for item in failures:
                lines.append(f"- `{item.method} {item.url}`: {item.note or item.response_preview}")

        lines.extend(["", "## Files", ""])
        lines.append(f"- JSON report: `{REPORT_JSON.relative_to(ROOT)}`")
        lines.append(f"- Markdown report: `{REPORT_MD.relative_to(ROOT)}`")
        return "\n".join(lines) + "\n"


def main() -> int:
    tester = EndpointTester()
    try:
        return tester.run()
    except TestFailure as exc:
        tester.results.append(
            EndpointResult(
                name="Fatal setup failure",
                method="N/A",
                url="N/A",
                status_code=None,
                ok=False,
                expected_status=[],
                duration_ms=0,
                note=str(exc),
                response_preview=str(exc),
            )
        )
        tester.context["finished_at"] = datetime.now(timezone.utc).isoformat()
        tester._write_reports()
        print(str(exc), file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
