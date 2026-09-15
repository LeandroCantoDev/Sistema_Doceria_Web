from django.db import models

class Produto(models.Model):
    name = models.CharField(max_length=100)
    price = models.FloatField()
    def __str__(self):
        return self.name
    

class Cliente(models.Model):
    name = models.CharField(max_length=50)
    def __str__(self):
        return self.name

class Pedido(models.Model):
    client = models.ForeignKey(Cliente, on_delete=models.CASCADE)
    boleto = models.BooleanField()
    def __str__(self):
        return f'Pedido de {self.client}'

class ItemPedido(models.Model):
    pedido = models.ForeignKey(Pedido, on_delete=models.CASCADE)
    produto = models.ForeignKey(Produto, on_delete=models.CASCADE)
    quantity = models.IntegerField()