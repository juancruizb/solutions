from django.db import models


class Topic(models.Model):
    """
    Represents an SDP Cloud solution topic (category).
    Populated by the sync_solutions management command.
    """
    sdp_id   = models.CharField(max_length=50, unique=True)
    name     = models.CharField(max_length=100)
    icon_key = models.CharField(max_length=100, blank=True)

    class Meta:
        ordering = ['name']

    def __str__(self):
        return self.name

    @property
    def solution_count(self):
        return self.solutions.count()


class Solution(models.Model):
    """
    Local copy of an SDP Cloud solution.
    Populated by: python manage.py sync_solutions
    Acts as a persistent cache — no Zoho token needed at query time.
    """
    sdp_id     = models.CharField(max_length=50, unique=True, db_index=True)
    display_id = models.CharField(max_length=20, blank=True)
    title      = models.CharField(max_length=500)
    description = models.TextField(blank=True)
    topic      = models.ForeignKey(
        Topic,
        null=True, blank=True,
        on_delete=models.SET_NULL,
        related_name='solutions',
    )
    status     = models.CharField(max_length=50, blank=True)
    author     = models.CharField(max_length=200, blank=True)
    updated_sdp = models.CharField(max_length=100, blank=True,
                                   help_text="Display value from SDP (e.g. 'Mar 29, 2023')")
    hits       = models.IntegerField(default=0)
    keywords   = models.CharField(max_length=500, blank=True)
    is_public  = models.BooleanField(default=False)
    synced_at  = models.DateTimeField(auto_now=True,
                                      help_text="Last time this record was synced from SDP")

    class Meta:
        ordering = ['-sdp_id']

    def __str__(self):
        return f"{self.display_id} — {self.title}"
