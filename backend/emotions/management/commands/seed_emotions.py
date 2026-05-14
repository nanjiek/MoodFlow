from datetime import timedelta

from django.core.management.base import BaseCommand
from django.db import transaction
from django.utils import timezone

from emotions.models import AppUser, EmotionAnalysis, EmotionRecord, EmotionTag


MOODFLOW_TAGS = (
    ("happy", "开心", 10),
    ("calm", "平静", 20),
    ("expecting", "期待", 30),
    ("anxious", "焦虑", 40),
    ("sad", "难过", 50),
    ("irritable", "烦躁", 60),
    ("plain", "平淡", 70),
    ("tired", "疲惫", 80),
)


DEMO_USERS = (
    {"external_id": "demo-user-001", "nickname": "小满", "gender": AppUser.GENDER_FEMALE},
    {"external_id": "demo-user-002", "nickname": "阿川", "gender": AppUser.GENDER_MALE},
)


DEMO_RECORDS = (
    {
        "external_id": "demo-user-001",
        "tag": "happy",
        "emotion_text": "今天完成了重要任务，感觉轻松又开心。",
        "emoji_id": "smile",
        "analysis": {
            "predicted_label": "happy",
            "confidence": 0.93,
            "keywords": ["完成任务", "轻松", "开心"],
            "intensity": 8,
            "trend": EmotionAnalysis.TREND_RISING,
            "cause": "任务完成带来的成就感。",
        },
    },
    {
        "external_id": "demo-user-001",
        "tag": "calm",
        "emotion_text": "晚上散步后心情平静了很多。",
        "emoji_id": "calm",
        "analysis": {
            "predicted_label": "calm",
            "confidence": 0.88,
            "keywords": ["散步", "平静"],
            "intensity": 5,
            "trend": EmotionAnalysis.TREND_STABLE,
            "cause": "规律放松活动缓解了情绪波动。",
        },
    },
    {
        "external_id": "demo-user-002",
        "tag": "anxious",
        "emotion_text": "明天要做汇报，有点担心自己讲不好。",
        "emoji_id": "nervous",
        "analysis": {
            "predicted_label": "anxious",
            "confidence": 0.9,
            "keywords": ["汇报", "担心"],
            "intensity": 7,
            "trend": EmotionAnalysis.TREND_RISING,
            "cause": "即将到来的公开表达任务带来压力。",
        },
    },
)


class Command(BaseCommand):
    help = "初始化 MoodFlow 8 类情绪标签和少量 demo 用户/情绪记录。"

    @transaction.atomic
    def handle(self, *args, **options):
        tag_map = {}
        for code, name, sort_order in MOODFLOW_TAGS:
            tag, _ = EmotionTag.objects.update_or_create(
                code=code,
                defaults={"name": name, "sort_order": sort_order, "is_active": True},
            )
            tag_map[code] = tag

        user_map = {}
        for payload in DEMO_USERS:
            user, _ = AppUser.objects.update_or_create(
                external_id=payload["external_id"],
                defaults={"nickname": payload["nickname"], "gender": payload["gender"], "is_active": True},
            )
            user_map[payload["external_id"]] = user

        created_records = 0
        now = timezone.now()
        for index, payload in enumerate(DEMO_RECORDS):
            user = user_map[payload["external_id"]]
            tag = tag_map[payload["tag"]]
            record, created = EmotionRecord.objects.get_or_create(
                user=user,
                emotion_text=payload["emotion_text"],
                defaults={
                    "tag": tag,
                    "emoji_id": payload["emoji_id"],
                    "recorded_at": now - timedelta(hours=index * 6),
                    "source": EmotionRecord.SOURCE_MANUAL,
                },
            )
            if created:
                created_records += 1

            analysis_payload = payload["analysis"]
            EmotionAnalysis.objects.update_or_create(
                record=record,
                defaults={
                    **analysis_payload,
                    "model_version": "demo-v1",
                    "raw_result": {"seed": True, "label": analysis_payload["predicted_label"]},
                },
            )

        self.stdout.write(
            self.style.SUCCESS(
                f"Seeded {len(tag_map)} emotion tags, {len(user_map)} demo users, {created_records} new records."
            )
        )
