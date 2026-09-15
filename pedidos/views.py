from django.shortcuts import render, redirect
from .models import Produto, Cliente, Pedido


def home(request):
    if request.method == 'POST':
        if 'price' in request.POST:
            name = request.POST['name']
            price = float(request.POST['price'])
            Produto.objects.create(name = name, price = price)
        else: 
            name = request.POST['name']
            Cliente.objects.create(name = name)
        return redirect('home')
    produtos = Produto.objects.all()
    clientes = Cliente.objects.all()
    return render(request, 'pedidos/home.html', {'produtos': produtos, 'clientes': clientes}) 

def criar_pedido(request):
    clientes = Cliente.objects.all()
    if request.method == 'POST':
        request.session['cliente_id'] =  request.POST['cliente_id']
        return redirect('adicionar_item')
    return render(request, 'pedidos/criar_pedido.html', {'clientes': clientes})

def adicionar_item(request):
    produtos = Produto.objects.all()
    if 'itens' not in request.session: 
        request.session['itens'] = []
    itens = request.session['itens']
    itens_detalhados = []
    for item in itens:
        produto_encontrado = Produto.objects.get(id=item['produto_id'])     
        itens_detalhados.append({'produto': produto_encontrado, 'quantidade':item['quantidade']})
    if request.method == 'POST':
        produto_id = request.POST['produto_id']
        quantidade = int(request.POST['quantidade'])
        request.session['itens'].append({'produto_id':produto_id, 'quantidade':quantidade})
    request.session.modified = True

    return render(request, 'pedidos/adicionar_item.html', {
    'produtos': produtos, 
    'itens': itens,
    'itens_detalhados': itens_detalhados
    })