import datetime
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('pedidos', '0004_pedido_assinatura'),
    ]

    operations = [
        migrations.AddField(
            model_name='pedido',
            name='data_criacao',
            field=models.DateTimeField(auto_now_add=True, default=datetime.datetime(2026, 9, 25, 0, 19, 10, 609101, tzinfo=datetime.timezone.utc)),
            preserve_default=False,
        ),
    ]
