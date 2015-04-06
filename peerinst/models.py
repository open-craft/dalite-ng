from django.db import models

class Assignment(models.Model):
    identifier = models.CharField(primary_key=True, max_length=100)
    name = models.CharField(max_length=200)

    def __unicode__(self):
        return self.identifier

class Question(models.Model):
    assignment = models.ForeignKey(Assignment)
    title = models.CharField(primary_key=True, max_length=100)
    primary_image = models.ImageField(blank=True, null=True, upload_to='images')
    primary_video_url = models.URLField(blank=True)
    secondary_image = models.ImageField(blank=True, null=True, upload_to='images')
    secondary_video_url = models.URLField(blank=True, max_length=200)
    ALPHA = 0
    NUMERIC = 1
    ANSWER_STYLE_CHOICES = (
        (ALPHA, 'alphabetic'),
        (NUMERIC, 'numeric'),
    )
    answer_style = models.IntegerField(choices=ANSWER_STYLE_CHOICES)
    answer_num_choices = models.PositiveSmallIntegerField()
    example_rationale = models.TextField()

    def __unicode__(self):
        return self.title
