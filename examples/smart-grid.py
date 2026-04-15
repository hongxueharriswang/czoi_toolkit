from django.db import models
from czoi.core.models import Zone
from czoi.core.models import CZOIEntity

class Substation(Zone):
    """A substation zone (child of a City or Region)."""
    voltage_kv = models.FloatField(help_text="Voltage in kilovolts")
    capacity_mw = models.FloatField(help_text="Maximum capacity in MW")

class Feeder(Zone):
    """A feeder zone (child of a Substation)."""
    max_current_a = models.FloatField(help_text="Maximum current in Amperes")
    current_load_a = models.FloatField(default=0.0)
    length_km = models.FloatField(help_text="Length of feeder line")

class SensorReading(CZOIEntity):
    """Real-time sensor reading from a feeder."""
    feeder = models.ForeignKey(Feeder, on_delete=models.CASCADE, related_name='readings')
    timestamp = models.DateTimeField(auto_now_add=True)
    current_a = models.FloatField()
    voltage_kv = models.FloatField()
    frequency_hz = models.FloatField()

class LoadForecast(CZOIEntity):
    """Stored forecast for a feeder (produced by neural component)."""
    feeder = models.ForeignKey(Feeder, on_delete=models.CASCADE)
    forecast_date = models.DateField()
    predicted_load = models.JSONField()  # list of hourly values
    created_at = models.DateTimeField(auto_now_add=True)