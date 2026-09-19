from django.shortcuts import render, redirect
from .models import Produto, Cliente, Pedido, ItemPedido


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

def finalizar_pedido(request):
    if request.method == 'GET':
        cliente_encontrado = Cliente.objects.get(id=request.session['cliente_id'])
        if 'itens' not in request.session:
            request.session['itens'] = []
        itens = request.session['itens']
        itens_detalhados = []
        total = 0
        for item in itens:
            produto_encontrado = Produto.objects.get(id = item['produto_id'])
            subtotal = produto_encontrado.price * item['quantidade']
            itens_detalhados.append({'produto': produto_encontrado, 'quantidade':item['quantidade'], 'subtotal': subtotal})
            total += subtotal
    if request.method == 'POST':
        cliente_encontrado = Cliente.objects.get(id=request.session['cliente_id'])
        if request.POST['boleto'].startswith('S'):
            boleto_valor = True
        else:
            boleto_valor = False
        pedido_criado = Pedido.objects.create(client = cliente_encontrado, boleto = boleto_valor)
        for item in request.session['itens']:
            produto_buscado = Produto.objects.get(id=item['produto_id'])
            ItemPedido.objects.create(pedido=pedido_criado, produto=produto_buscado, quantity=item['quantidade'])
        del request.session['cliente_id']
        del request.session['itens']
        return redirect('home')


    return render(
        request, 
        'pedidos/finalizar_pedido.html', 
        {
         'itens_detalhados': itens_detalhados, 
         'cliente':cliente_encontrado, 
         'total': total,
         })
