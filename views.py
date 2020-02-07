from django.db.models import FloatField, ExpressionWrapper, F, Sum
from dynamic.models import Car
from decimal import Decimal
from django.db.models.functions import Cast

class CarViewSet(BaseViewSet):
    serializer_class = CarSerializer

    def get_queryset(self):
        q = Car.objects.all()
        make = 'honda'
        model = 'civic'
        q = Car.objects.filter(~Q(condition='new') & Q(year__isnull=False)).filter(make__iexact=make, model__iexact=model)
        
        yq = q.aggregate(Sum('year'))
        year__sum = yq['year__sum']
        
        aq = q.aggregate(Sum('amount'))
        amount__sum = aq['amount__sum']

        kq = q.aggregate(Sum('kilometers'))
        kilometers__sum = kq['kilometers__sum']
        
        return q.annotate(
                total_of_weights=ExpressionWrapper(
                    (F('year') * 1.0 / year__sum) + 
                    (F('amount') * 1.0 / amount__sum) +
                    (F('kilometers') * 1.0 / kilometers__sum),
                    output_field=FloatField()
                ),
        ).order_by('-weight', '-total_of_weights')
