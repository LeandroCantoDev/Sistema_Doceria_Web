from django.db import models

from django.utils import timezone

class Produto(models.Model):
    name = models.CharField(max_length=100)
    price = models.FloatField()
    def __str__(self):
        return self.name
    

class Cliente(models.Model):
    name = models.CharField(max_length=50)
    def __str__(self):
        return self.name

FORMAS_PAGAMENTO = [
    ('DINHEIRO', 'Dinheiro'),
    ('CONSIGNADO', 'Consignado'),
    ('PIX', 'Pix'),
    ('BOLETO', 'Boleto'),
]

class Pedido(models.Model):
    client = models.ForeignKey(Cliente, on_delete=models.CASCADE)
    forma_pagamento = models.CharField(max_length=20, choices=FORMAS_PAGAMENTO, default='DINHEIRO')
    boleto = models.BooleanField(default=False)
    boleto_arquivo = models.FileField(upload_to='boletos/', blank=True, null=True)
    assinatura = models.TextField(blank=True, null=True)
    data_criacao = models.DateTimeField(default=timezone.now)

    def save(self, *args, **kwargs):
        if self.forma_pagamento == 'BOLETO':
            self.boleto = True
        else:
            self.boleto = False
        super().save(*args, **kwargs)

    def __str__(self):
        return f'Pedido de {self.client}'

    @property
    def total(self):
        return sum(item.produto.price * item.quantity for item in self.itempedido_set.all())

    @property
    def esta_assinado(self):
        return bool(self.assinatura)

    @property
    def tem_boleto_arquivo(self):
        return bool(self.boleto_arquivo)

class ItemPedido(models.Model):
    pedido = models.ForeignKey(Pedido, on_delete=models.CASCADE)
    produto = models.ForeignKey(Produto, on_delete=models.CASCADE)
    quantity = models.IntegerField()


