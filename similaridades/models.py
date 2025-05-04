from django.db import models

class TextoEvento(models.Model):
    id = models.AutoField(primary_key=True)
    evento = models.CharField(max_length=255)
    descricao = models.TextField()
    ano = models.IntegerField()

    def __str__(self):
        return self.evento[:50]