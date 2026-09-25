from django.urls import path
from . import views

urlpatterns = [
    path('', views.home, name='home'),
    path('editar-produto/<int:produto_id>/', views.editar_produto, name='editar_produto'),
    path('excluir-produto/<int:produto_id>/', views.excluir_produto, name='excluir_produto'),
    path('editar-cliente/<int:cliente_id>/', views.editar_cliente, name='editar_cliente'),
    path('excluir-cliente/<int:cliente_id>/', views.excluir_cliente, name='excluir_cliente'),
    path('criar-pedido/', views.criar_pedido, name='criar_pedido'),
    path('adicionar-item/', views.adicionar_item, name='adicionar_item'),
    path('remover-item/<int:item_index>/', views.remover_item, name='remover_item'),
    path('finalizar-pedido/', views.finalizar_pedido, name='finalizar_pedido'),
    path('assinar/<int:pedido_id>/', views.assinar_pedido, name='assinar_pedido'),
    path('pedido-concluido/', views.pedido_concluido, name='pedido_concluido'),
    path('pedido-pronto/<int:pedido_id>/', views.pedido_pronto, name='pedido_pronto'),
    path('gerar-pdf/<int:pedido_id>/', views.gerar_pdf, name='gerar_pdf'),
    path('ultimos-pedidos/', views.ultimos_pedidos, name='ultimos_pedidos'),
    path('excluir-pedido/<int:pedido_id>/', views.excluir_pedido, name='excluir_pedido'),
]



