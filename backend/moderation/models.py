from django.db import models
from django.utils.translation import gettext_lazy as _


class TreeHolePost(models.Model):
    class Status(models.TextChoices):
        PENDING = "pending", _("Pending")
        APPROVED = "approved", _("Approved")
        REJECTED = "rejected", _("Rejected")

    user = models.ForeignKey(
        "emotions.AppUser",
        related_name="tree_hole_posts",
        on_delete=models.CASCADE,
        null=True,
        blank=True,
    )
    anonymous_id = models.CharField(max_length=64, blank=True, db_index=True)
    content = models.TextField()
    emotion_tag = models.ForeignKey(
        "emotions.EmotionTag",
        related_name="tree_hole_posts",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
    )
    status = models.CharField(
        max_length=16,
        choices=Status.choices,
        default=Status.PENDING,
        db_index=True,
    )
    reject_reason = models.TextField(blank=True)
    reviewed_by = models.ForeignKey(
        "emotions.AppUser",
        related_name="reviewed_tree_hole_posts",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
    )
    reviewed_at = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True, db_index=True)

    class Meta:
        db_table = "moderation_tree_hole_post"
        ordering = ["-created_at"]
        indexes = [
            models.Index(fields=["status", "-created_at"]),
            models.Index(fields=["emotion_tag", "status"]),
        ]

    def __str__(self):
        return f"TreeHolePost<{self.pk}> {self.status}"


class TreeHoleComment(models.Model):
    post = models.ForeignKey(
        TreeHolePost,
        related_name="comments",
        on_delete=models.CASCADE,
    )
    user = models.ForeignKey(
        "emotions.AppUser",
        related_name="tree_hole_comments",
        on_delete=models.CASCADE,
        null=True,
        blank=True,
    )
    anonymous_id = models.CharField(max_length=64, blank=True, db_index=True)
    content = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True, db_index=True)

    class Meta:
        db_table = "moderation_tree_hole_comment"
        ordering = ["created_at"]

    def __str__(self):
        return f"TreeHoleComment<{self.pk}> post={self.post_id}"
