from django.urls import path
from . import views

urlpatterns = [
    path('', views.home, name='home'),
    path('criar-pedido/', views.criar_pedido, name='criar_pedido'),
    path('adicionar-item/', views.adicionar_item, name='adicionar_item'),
    path('finalizar-pedido/', views.finalizar_pedido, name='finalizar_pedido')
]