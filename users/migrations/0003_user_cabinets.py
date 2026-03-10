from django.db import migrations, models


def copier_cabinet_vers_cabinets(apps, schema_editor):
    User = apps.get_model('users', 'User')
    for user in User.objects.filter(cabinet__isnull=False):
        user.cabinets.add(user.cabinet_id)


def reverse_copier(apps, schema_editor):
    pass


class Migration(migrations.Migration):

    dependencies = [
        ('users', '0002_cabinet_user_cabinet'),
    ]

    operations = [
        # 1. Libérer le related_name 'Comptables' de l'ancien FK
        migrations.AlterField(
            model_name='user',
            name='cabinet',
            field=models.ForeignKey(
                blank=True,
                null=True,
                on_delete=models.deletion.SET_NULL,
                related_name='cabinet_fk_old',
                to='users.cabinet',
                verbose_name='Cabinet',
            ),
        ),
        # 2. Ajouter le nouveau champ ManyToMany avec related_name 'Comptables'
        migrations.AddField(
            model_name='user',
            name='cabinets',
            field=models.ManyToManyField(
                blank=True,
                related_name='Comptables',
                to='users.cabinet',
                verbose_name='Cabinets',
            ),
        ),
        # 3. Copier les données existantes
        migrations.RunPython(copier_cabinet_vers_cabinets, reverse_copier),
        # 4. Supprimer l'ancien champ ForeignKey
        migrations.RemoveField(
            model_name='user',
            name='cabinet',
        ),
    ]
