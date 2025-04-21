from django.db import models

class TextoEvento(models.Model):
    evento = models.CharField(max_length=255)
    descricao = models.TextField()
    ano = models.IntegerField()

    def __str__(self):
        return self.evento[:50]