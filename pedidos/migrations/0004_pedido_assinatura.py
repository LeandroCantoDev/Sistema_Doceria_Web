from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('pedidos', '0003_itempedido'),
    ]

    operations = [
        migrations.AddField(
            model_name='pedido',
            name='assinatura',
            field=models.TextField(blank=True, null=True),
        ),
    ]
