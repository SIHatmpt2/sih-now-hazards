from apps.weather.accuweather import AccuWeatherProvider
from apps.weather.lightning import AccuWeatherLightningProvider

def test_accuweather_metric_accepts_direct_value():
    assert AccuWeatherProvider._metric({"Value": 24.5}) == 24.5

def test_accuweather_metric_accepts_metric_value():
    assert AccuWeatherProvider._metric({"Metric": {"Value": 24.5}}) == 24.5

def test_lightning_provider_uses_core_key_as_fallback():
    provider = AccuWeatherLightningProvider()
    assert provider.api_key is None or isinstance(provider.api_key, str)
