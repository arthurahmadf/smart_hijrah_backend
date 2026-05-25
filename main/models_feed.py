from django.db import models
from django.conf import settings

class Feed(models.Model):
    """Model untuk postingan feed"""
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='feeds')
    caption = models.TextField(blank=True, null=True)
    location = models.CharField(max_length=255, blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    # Stats
    like_count = models.IntegerField(default=0)
    comment_count = models.IntegerField(default=0)
    
    # Metadata
    is_sponsored = models.BooleanField(default=False)
    permalink = models.CharField(max_length=500, blank=True, null=True)
    
    class Meta:
        db_table = 'social_feed'
        ordering = ['-created_at']
    
    def __str__(self):
        return f"Feed by {self.user.username} at {self.created_at}"

class FeedPicture(models.Model):
    """Gambar untuk feed (bisa multiple)"""
    feed = models.ForeignKey(Feed, on_delete=models.CASCADE, related_name='pictures')
    image = models.ImageField(upload_to='feed_pictures/')
    order = models.IntegerField(default=0)
    
    class Meta:
        db_table = 'social_feed_picture'
        ordering = ['order']
    
    def __str__(self):
        return f"Picture for feed {self.feed.id}"

class FeedLike(models.Model):
    """Like pada feed"""
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    feed = models.ForeignKey(Feed, on_delete=models.CASCADE, related_name='likes')
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        db_table = 'social_feed_like'
        unique_together = ('user', 'feed')
    
    def __str__(self):
        return f"{self.user.username} likes feed {self.feed.id}"

class FeedComment(models.Model):
    """Comment pada feed"""
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    feed = models.ForeignKey(Feed, on_delete=models.CASCADE, related_name='comments')
    text = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        db_table = 'social_feed_comment'
        ordering = ['created_at']
    
    def __str__(self):
        return f"Comment by {self.user.username} on feed {self.feed.id}"

class Follow(models.Model):
    """User following relationship"""
    follower = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='following')
    following = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='followers')
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        db_table = 'social_follow'
        unique_together = ('follower', 'following')
    
    def __str__(self):
        return f"{self.follower.username} follows {self.following.username}"

class Story(models.Model):
    """Model untuk stories (Instagram-like)"""
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='stories')
    media_url = models.URLField(max_length=500)  # Link ke video/gambar
    media_type = models.CharField(max_length=10, choices=[('image', 'Image'), ('video', 'Video')], default='image')
    created_at = models.DateTimeField(auto_now_add=True)
    expires_at = models.DateTimeField()  # Story expired after 24 hours
    
    class Meta:
        db_table = 'social_story'
        ordering = ['-created_at']
    
    def __str__(self):
        return f"Story by {self.user.username} at {self.created_at}"

class StorySeen(models.Model):
    """Track siapa saja yang sudah melihat story"""
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    story = models.ForeignKey(Story, on_delete=models.CASCADE, related_name='seen_by')
    seen_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        db_table = 'social_story_seen'
        unique_together = ('user', 'story')
    
    def __str__(self):
        return f"{self.user.username} seen story {self.story.id}"

class FeedComment(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    feed = models.ForeignKey(Feed, on_delete=models.CASCADE, related_name='comments')
    text = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        db_table = 'social_feed_comment'
        ordering = ['created_at']