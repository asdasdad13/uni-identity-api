from django.db import models

class Identity(models.Model):
    legal_forenames = models.CharField( max_length=200,
                                        help_text='All given names and middle names exactly as they appear on the official ID.',
                                        null=True,
                                        blank=False,
                                        unique=False
                                    )
    legal_surname = models.CharField(  max_length=100,
                                        help_text='The surname exactly as it appears on the official ID (passport).',
                                        null=True,
                                        blank=False,
                                        unique=False
                                    )
    preferred_name = models.CharField(  max_length=200,
                                        help_text='Given by the user.',
                                        blank=True,
                                        null=True,
                                        unique=False
    ) # In the actual implementation, this is supposed to be under Profile schema
    
    class Meta:
        verbose_name_plural = "Identities"