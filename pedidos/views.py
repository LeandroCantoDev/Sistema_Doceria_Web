from xhtml2pdf import pisa
from django.template.loader import get_template
from django.http import HttpResponse
from django.shortcuts import render, redirect, get_object_or_404
from django.urls import reverse
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

def editar_produto(request, produto_id):
    produto = get_object_or_404(Produto, id=produto_id)
    if request.method == 'POST':
        produto.name = request.POST.get('name')
        produto.price = float(request.POST.get('price'))
        produto.save()
        return redirect('home')
    return render(request, 'pedidos/editar_produto.html', {'produto': produto})

def excluir_produto(request, produto_id):
    Produto.objects.filter(id=produto_id).delete()
    return redirect('home')

def editar_cliente(request, cliente_id):
    cliente = get_object_or_404(Cliente, id=cliente_id)
    if request.method == 'POST':
        cliente.name = request.POST.get('name')
        cliente.save()
        return redirect('home')
    return render(request, 'pedidos/editar_cliente.html', {'cliente': cliente})

def excluir_cliente(request, cliente_id):
    Cliente.objects.filter(id=cliente_id).delete()
    return redirect('home') 

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

    if request.method == 'POST':
        produto_id = request.POST['produto_id'] 
        quantidade = int(request.POST['quantidade'])
        request.session['itens'].append({'produto_id': produto_id, 'quantidade': quantidade})
        request.session.modified = True
        return redirect('adicionar_item')

    itens = request.session['itens']
    itens_detalhados = []
    total_parcial = 0
    for idx, item in enumerate(itens):
        produto_encontrado = Produto.objects.get(id=item['produto_id'])     
        subtotal = produto_encontrado.price * item['quantidade']
        itens_detalhados.append({
            'index': idx,
            'produto': produto_encontrado,
            'quantidade': item['quantidade'],
            'subtotal': subtotal
        })
        total_parcial += subtotal

    return render(request, 'pedidos/adicionar_item.html', {
        'produtos': produtos, 
        'itens': itens,
        'itens_detalhados': itens_detalhados,
        'total_parcial': total_parcial
    })

def remover_item(request, item_index):
    if 'itens' in request.session:
        itens = request.session['itens']
        if 0 <= item_index < len(itens):
            itens.pop(item_index)
            request.session.modified = True
    return redirect('adicionar_item')

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
        return redirect('pedido_pronto', pedido_id=pedido_criado.id)


    return render(
        request, 
        'pedidos/finalizar_pedido.html', 
        {
         'itens_detalhados': itens_detalhados, 
         'cliente':cliente_encontrado, 
         'total': total,
         })


def assinar_pedido(request, pedido_id):
    pedido_encontrado = Pedido.objects.select_related('client').get(id=pedido_id)
    itens = ItemPedido.objects.filter(pedido=pedido_encontrado).select_related('produto')
    itens_detalhados = []
    total = 0
    for item in itens:
        produto_encontrado = item.produto
        subtotal = produto_encontrado.price * item.quantity
        itens_detalhados.append({'produto': produto_encontrado, 'quantidade': item.quantity, 'subtotal': subtotal})
        total += subtotal

    if request.method == 'POST':
        if not pedido_encontrado.assinatura and 'assinatura_dados' in request.POST:
            pedido_encontrado.assinatura = request.POST['assinatura_dados']
            pedido_encontrado.save()
        return redirect('pedido_concluido')

    return render(
        request,
        'pedidos/assinar_pedido.html',
        {
            'pedido': pedido_encontrado,
            'itens_detalhados': itens_detalhados,
            'total': total,
        }
    )

def pedido_concluido(request):
    return render(request, 'pedidos/pedido_concluido.html')

def pedido_pronto(request, pedido_id):
    pedido_encontrado = Pedido.objects.get(id= pedido_id)
    link_assinatura = request.build_absolute_uri(reverse('assinar_pedido', args=[pedido_encontrado.id]))
    link_whats = f'https://wa.me/?text=Segue o resumo do seu pedido, assine aqui: {link_assinatura}'
    return render (request,
                   'pedidos/pedido_pronto.html',
                   {
                   'link_whats': link_whats,
                   'link_assinatura': link_assinatura,
                   'pedido_encontrado': pedido_encontrado
                   })    


def gerar_pdf(request, pedido_id):
    itens_detalhados = []
    total = 0
    pedido_encontrado = Pedido.objects.get(id=pedido_id)
    itens = ItemPedido.objects.filter(pedido=pedido_encontrado)
    for item in itens:
        produto_encontrado = item.produto
        subtotal = produto_encontrado.price * item.quantity
        itens_detalhados.append({'produto': produto_encontrado, 'quantidade': item.quantity, 'subtotal': subtotal})
        total += subtotal
    template = get_template('pedidos/pdf_pedidos.html')
    html = template.render({'pedido': pedido_encontrado, 'itens_detalhados': itens_detalhados, 'total': total})
    response = HttpResponse(content_type='application/pdf')
    pisa.CreatePDF(html, dest=response)
    return response

def ultimos_pedidos(request):
    busca = request.GET.get('busca', '').strip()
    pedidos = Pedido.objects.select_related('client').prefetch_related('itempedido_set__produto').order_by('-id')
    if busca:
        pedidos = pedidos.filter(client__name__icontains=busca)
    else:
        pedidos = pedidos[:30]
    return render(request, 'pedidos/ultimos_pedidos.html', {'pedidos': pedidos, 'busca': busca})

def excluir_pedido(request, pedido_id):
    Pedido.objects.filter(id=pedido_id).delete()
    return redirect('ultimos_pedidos')