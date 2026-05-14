from django.apps import apps
from django.core.management.base import BaseCommand
from django.db import OperationalError, ProgrammingError, transaction
from django.utils import timezone

from moderation.models import TreeHoleComment, TreeHolePost


class Command(BaseCommand):
    help = "Seed sample tree hole posts for moderation review."

    def handle(self, *args, **options):
        user = _first_instance("emotions", "AppUser")
        reviewer = user
        emotion_tags = _first_instances("emotions", "EmotionTag", limit=3)
        now = timezone.now()

        samples = [
            {
                "anonymous_id": "tree-hole-pending-001",
                "content": "今天情绪有点低落，想找个地方把话说出来。",
                "status": TreeHolePost.Status.PENDING,
                "reject_reason": "",
                "reviewed_by": None,
                "reviewed_at": None,
                "emotion_tag": _tag_at(emotion_tags, 0),
            },
            {
                "anonymous_id": "tree-hole-approved-001",
                "content": "完成了拖延很久的小目标，感觉终于松了一口气。",
                "status": TreeHolePost.Status.APPROVED,
                "reject_reason": "",
                "reviewed_by": reviewer,
                "reviewed_at": now,
                "emotion_tag": _tag_at(emotion_tags, 1),
            },
            {
                "anonymous_id": "tree-hole-rejected-001",
                "content": "这条样例用于模拟不适合展示的树洞内容。",
                "status": TreeHolePost.Status.REJECTED,
                "reject_reason": "样例驳回：内容不适合公开展示。",
                "reviewed_by": reviewer,
                "reviewed_at": now,
                "emotion_tag": _tag_at(emotion_tags, 2),
            },
        ]

        created_count = 0
        updated_count = 0
        with transaction.atomic():
            for sample in samples:
                post, created = TreeHolePost.objects.update_or_create(
                    anonymous_id=sample["anonymous_id"],
                    defaults={
                        "user": user,
                        "content": sample["content"],
                        "emotion_tag": sample["emotion_tag"],
                        "status": sample["status"],
                        "reject_reason": sample["reject_reason"],
                        "reviewed_by": sample["reviewed_by"],
                        "reviewed_at": sample["reviewed_at"],
                    },
                )
                if sample["status"] == TreeHolePost.Status.APPROVED:
                    TreeHoleComment.objects.update_or_create(
                        post=post,
                        anonymous_id="tree-hole-comment-001",
                        defaults={
                            "user": user,
                            "content": "谢谢你愿意分享，也祝你继续保持这份轻松。",
                        },
                    )
                if created:
                    created_count += 1
                else:
                    updated_count += 1

        self.stdout.write(
            self.style.SUCCESS(
                f"Seeded tree hole posts: created={created_count}, updated={updated_count}",
            ),
        )


def _first_instance(app_label, model_name):
    instances = _first_instances(app_label, model_name, limit=1)
    return instances[0] if instances else None


def _first_instances(app_label, model_name, limit):
    try:
        model = apps.get_model(app_label, model_name)
    except (LookupError, RuntimeError):
        return []

    try:
        return list(model.objects.all()[:limit])
    except (OperationalError, ProgrammingError):
        return []


def _tag_at(tags, index):
    if index < len(tags):
        return tags[index]
    return tags[0] if tags else None
