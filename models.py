
class Car(Base):
    image = models.TextField(blank=True, null=True)
    title = models.CharField(max_length=255, blank=True, null=True)
    description = models.TextField(blank=True, null=True)
    listing_id = models.PositiveIntegerField()
    link = models.URLField(max_length=255, blank=True, null=True)
    territory = models.CharField(max_length=255, blank=True, null=True)
    weight = models.PositiveIntegerField(default=0, blank=True, null=True)
    amount = models.PositiveIntegerField(default=0, blank=True, null=True)
    address = models.TextField(blank=True, null=True)
    year = models.PositiveIntegerField(blank=True, null=True)
    make = models.CharField(max_length=255, blank=True, null=True)
    model = models.CharField(max_length=255, blank=True, null=True)
    transmission = models.CharField(max_length=255, blank=True, null=True)
    drivetrain = models.CharField(max_length=255, blank=True, null=True)
    kilometers = models.PositiveIntegerField(blank=True, null=True)
    condition = models.CharField(max_length=255, blank=True, null=True)

    class Meta:
        verbose_name = _('Car')
        verbose_name_plural = _('Cars')
