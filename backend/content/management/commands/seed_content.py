from django.apps import apps
from django.core.management.base import BaseCommand, CommandError

from ...models import CompanionContent, SystemConfig


BASE_CONFIGS = {
    "push_frequency": {
        "value": {"times_per_day": 1},
        "description": "Default reminder pushes per day.",
        "is_public": True,
    },
    "reminder_window": {
        "value": {"start": "09:00", "end": "21:00"},
        "description": "Local time window for reminders.",
        "is_public": True,
    },
    "negative_emergency_days": {
        "value": {"days": 3},
        "description": "Consecutive negative-emotion days before emergency attention is suggested.",
        "is_public": False,
    },
}

EMOTION_CONTENT_PRESETS = {
    "anxious": (
        {
            "content_type": CompanionContent.CONTENT_TYPE_BREATHING,
            "title": "先把呼吸放慢一点",
            "body": "试着吸气 4 秒、停 2 秒、呼气 6 秒，连做 3 轮，先把身体从紧绷里拉回来。",
            "weight": 12,
        },
        {
            "content_type": CompanionContent.CONTENT_TYPE_ADVICE,
            "title": "只拆下一步就够了",
            "body": "把最担心的事写下来，再写一个十分钟内能完成的最小动作，先别要求自己一次解决全部。",
            "weight": 10,
        },
    ),
    "sad": (
        {
            "content_type": CompanionContent.CONTENT_TYPE_PHRASE,
            "title": "先允许自己低落一下",
            "body": "你不用立刻振作，先把难受放在这里，也是一种很重要的整理。",
            "weight": 12,
        },
        {
            "content_type": CompanionContent.CONTENT_TYPE_TEMPLATE,
            "title": "情绪日记小模板",
            "body": "今天让我最难受的是____。如果有人理解我，我最想让对方知道____。",
            "weight": 9,
        },
    ),
    "tired": (
        {
            "content_type": CompanionContent.CONTENT_TYPE_MUSIC,
            "title": "切到低刺激模式",
            "body": "把屏幕亮度调低一点，找一段轻音乐，给自己 10 分钟不处理消息的空档。",
            "weight": 12,
        },
        {
            "content_type": CompanionContent.CONTENT_TYPE_ADVICE,
            "title": "先补一点电",
            "body": "如果现在很累，先做一件最能恢复体力的小事，比如喝水、起身活动、闭眼休息两分钟。",
            "weight": 10,
        },
    ),
}


def _emotion_label(tag):
    for attr in ("name", "label", "code", "slug"):
        if hasattr(tag, attr):
            value = getattr(tag, attr)
            if value:
                return str(value)
    return str(tag.pk)


class Command(BaseCommand):
    help = "Seed companion content and base system configs."

    def handle(self, *args, **options):
        try:
            emotion_tag_model = apps.get_model("emotions", "EmotionTag")
        except LookupError as exc:
            raise CommandError("emotions.EmotionTag is required before seeding content.") from exc

        config_count = 0
        for key, defaults in BASE_CONFIGS.items():
            _, created = SystemConfig.objects.update_or_create(key=key, defaults=defaults)
            config_count += int(created)

        content_count = 0
        tags = list(emotion_tag_model.objects.all())
        if not tags:
            self.stdout.write(self.style.WARNING("No emotion tags found; only system configs were seeded."))

        for tag in tags:
            label = _emotion_label(tag)
            items = EMOTION_CONTENT_PRESETS.get(
                getattr(tag, "code", ""),
                (
                    {
                        "content_type": CompanionContent.CONTENT_TYPE_PHRASE,
                        "title": f"{label}时，先慢一点",
                        "body": "先做一个缓慢呼吸，再用一句话记下此刻最明显的感受。",
                        "weight": 10,
                    },
                    {
                        "content_type": CompanionContent.CONTENT_TYPE_ADVICE,
                        "title": f"{label}时的小下一步",
                        "body": "写下现在最需要的一件小事，然后只做第一步就好。",
                        "weight": 8,
                    },
                ),
            )
            for item in items:
                _, created = CompanionContent.objects.update_or_create(
                    emotion_tag=tag,
                    content_type=item["content_type"],
                    title=item["title"],
                    defaults={
                        "body": item["body"],
                        "resource_url": "",
                        "weight": item["weight"],
                        "is_active": True,
                    },
                )
                content_count += int(created)

        self.stdout.write(
            self.style.SUCCESS(
                f"Seed complete: {content_count} new companion contents, {config_count} new system configs."
            )
        )
