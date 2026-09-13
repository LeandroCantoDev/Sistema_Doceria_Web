from django.db import models

class Produto(models.Model):
    name = models.CharField(max_length=100)
    price = models.FloatField()


class Cliente(models.Model):
    name = models.CharField(max_length=50)


class Pedido(models.Model):
    client = models.ForeignKey(Cliente, on_delete=models.CASCADE)
    boleto = models.BooleanField()

class ItemPedido(models.Model):
    pedido = models.ForeignKey(Pedido, on_delete=models.CASCADE)
    produto = models.ForeignKey(Produto, on_delete=models.CASCADE)
    quantity = models.IntegerField()