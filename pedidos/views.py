from datetime import datetime
from django.utils import timezone
from django.core.paginator import Paginator
from django.db.models import Q
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
    if 'cliente_id' not in request.session:
        return redirect('criar_pedido')
    cliente_encontrado = Cliente.objects.get(id=request.session['cliente_id'])

    if request.method == 'GET':
        if 'itens' not in request.session:
            request.session['itens'] = []
        itens = request.session['itens']
        itens_detalhados = []
        total = 0
        for item in itens:
            produto_encontrado = Produto.objects.get(id=item['produto_id'])
            subtotal = produto_encontrado.price * item['quantidade']
            itens_detalhados.append({'produto': produto_encontrado, 'quantidade': item['quantidade'], 'subtotal': subtotal})
            total += subtotal
        data_hoje = timezone.localtime().strftime('%Y-%m-%d')
        return render(
            request, 
            'pedidos/finalizar_pedido.html', 
            {
             'itens_detalhados': itens_detalhados, 
             'cliente': cliente_encontrado, 
             'total': total,
             'data_hoje': data_hoje,
            })

    if request.method == 'POST':
        forma_pagamento = request.POST.get('forma_pagamento', 'DINHEIRO')
        if forma_pagamento not in ['DINHEIRO', 'CONSIGNADO', 'PIX', 'BOLETO']:
            if request.POST.get('boleto', '').startswith('S'):
                forma_pagamento = 'BOLETO'
            else:
                forma_pagamento = 'DINHEIRO'

        boleto_valor = (forma_pagamento == 'BOLETO')

        data_pedido_str = request.POST.get('data_pedido')
        data_criacao = timezone.now()
        if data_pedido_str:
            try:
                dt = datetime.strptime(data_pedido_str, '%Y-%m-%d')
                agora = timezone.localtime()
                dt = dt.replace(hour=agora.hour, minute=agora.minute, second=agora.second)
                data_criacao = timezone.make_aware(dt) if timezone.is_naive(dt) else dt
            except ValueError:
                pass

        pedido_criado = Pedido.objects.create(
            client=cliente_encontrado, 
            forma_pagamento=forma_pagamento,
            boleto=boleto_valor,
            data_criacao=data_criacao
        )
        for item in request.session.get('itens', []):
            produto_buscado = Produto.objects.get(id=item['produto_id'])
            ItemPedido.objects.create(pedido=pedido_criado, produto=produto_buscado, quantity=item['quantidade'])
        del request.session['cliente_id']
        del request.session['itens']
        return redirect('pedido_pronto', pedido_id=pedido_criado.id)


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
    nome_arquivo = f'pedido_{pedido_encontrado.id}_{pedido_encontrado.client.name.replace(" ", "_")}.pdf'
    response['Content-Disposition'] = f'inline; filename="{nome_arquivo}"'
    pisa_status = pisa.CreatePDF(html, dest=response, encoding='utf-8')
    if pisa_status.err:
        return HttpResponse('Erro ao gerar PDF', status=500)
    return response

def ultimos_pedidos(request):
    busca = request.GET.get('busca', '').strip()
    pagamento = request.GET.get('pagamento', 'TODOS').upper()

    pedidos = Pedido.objects.select_related('client').prefetch_related('itempedido_set__produto').order_by('-data_criacao', '-id')

    if busca:
        pedidos = pedidos.filter(client__name__icontains=busca)

    if pagamento in ['DINHEIRO', 'CONSIGNADO', 'PIX', 'BOLETO']:
        pedidos = pedidos.filter(forma_pagamento=pagamento)
    elif pagamento == 'BOLETO_PENDENTE':
        pedidos = pedidos.filter(forma_pagamento='BOLETO').filter(Q(boleto_arquivo__isnull=True) | Q(boleto_arquivo=''))
    elif pagamento == 'BOLETO_ANEXADO':
        pedidos = pedidos.filter(forma_pagamento='BOLETO').exclude(Q(boleto_arquivo__isnull=True) | Q(boleto_arquivo=''))

    # Paginação com 10 pedidos por página
    paginator = Paginator(pedidos, 10)
    page_number = request.GET.get('page', 1)
    pedidos_page = paginator.get_page(page_number)

    return render(request, 'pedidos/ultimos_pedidos.html', {
        'pedidos': pedidos_page,
        'busca': busca,
        'pagamento': pagamento,
    })

def anexar_boleto(request, pedido_id):
    pedido = get_object_or_404(Pedido.objects.select_related('client'), id=pedido_id)

    if request.method == 'POST':
        if 'remover_boleto' in request.POST:
            if pedido.boleto_arquivo:
                pedido.boleto_arquivo.delete(save=False)
                pedido.boleto_arquivo = None
                pedido.save()
            return redirect('ultimos_pedidos')

        if 'boleto_arquivo' in request.FILES:
            pedido.boleto_arquivo = request.FILES['boleto_arquivo']
            pedido.forma_pagamento = 'BOLETO'
            pedido.boleto = True
            pedido.save()
            return redirect('ultimos_pedidos')

    return render(request, 'pedidos/anexar_boleto.html', {'pedido': pedido})

def editar_pedido(request, pedido_id):
    pedido = get_object_or_404(Pedido.objects.select_related('client'), id=pedido_id)
    produtos = Produto.objects.all()

    if request.method == 'POST':
        # 1. Atualizar forma de pagamento
        forma_pagamento = request.POST.get('forma_pagamento')
        if forma_pagamento in ['DINHEIRO', 'CONSIGNADO', 'PIX', 'BOLETO']:
            pedido.forma_pagamento = forma_pagamento
            pedido.boleto = (forma_pagamento == 'BOLETO')

        # 2. Atualizar data de criação
        data_input = request.POST.get('data_criacao')
        if data_input:
            try:
                if 'T' in data_input:
                    dt = datetime.strptime(data_input, '%Y-%m-%dT%H:%M')
                else:
                    dt = datetime.strptime(data_input, '%Y-%m-%d')
                pedido.data_criacao = timezone.make_aware(dt) if timezone.is_naive(dt) else dt
            except ValueError:
                pass

        pedido.save()

        # 3. Adicionar novo item se preenchido
        novo_produto_id = request.POST.get('novo_produto_id')
        nova_quantidade = request.POST.get('nova_quantidade')
        if novo_produto_id and nova_quantidade:
            qtd = int(nova_quantidade)
            if qtd > 0:
                prod = Produto.objects.get(id=novo_produto_id)
                item_existente = ItemPedido.objects.filter(pedido=pedido, produto=prod).first()
                if item_existente:
                    item_existente.quantity += qtd
                    item_existente.save()
                else:
                    ItemPedido.objects.create(pedido=pedido, produto=prod, quantity=qtd)

        return redirect('editar_pedido', pedido_id=pedido.id)

    itens = ItemPedido.objects.filter(pedido=pedido).select_related('produto')
    itens_detalhados = []
    total = 0
    for item in itens:
        subtotal = item.produto.price * item.quantity
        itens_detalhados.append({
            'item': item,
            'subtotal': subtotal
        })
        total += subtotal

    data_formatada = timezone.localtime(pedido.data_criacao).strftime('%Y-%m-%dT%H:%M')

    return render(request, 'pedidos/editar_pedido.html', {
        'pedido': pedido,
        'produtos': produtos,
        'itens_detalhados': itens_detalhados,
        'total': total,
        'data_formatada': data_formatada,
    })

def remover_item_pedido(request, pedido_id, item_id):
    pedido = get_object_or_404(Pedido, id=pedido_id)
    ItemPedido.objects.filter(id=item_id, pedido=pedido).delete()
    return redirect('editar_pedido', pedido_id=pedido.id)

def excluir_pedido(request, pedido_id):
    Pedido.objects.filter(id=pedido_id).delete()
    return redirect('ultimos_pedidos')