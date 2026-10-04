from apps.weather.lightning import BhuvanLightningProvider


def test_bhuvan_lightning_provider_name():
    provider = BhuvanLightningProvider()
    assert provider.name == "bhuvan-nrsc-lightning"


def test_bhuvan_lightning_number_aliases_are_parsed():
    assert BhuvanLightningProvider._first_number({"flash_count": "42"}, ("flash_count",)) == 42.0


def test_bhuvan_lightning_datetime_is_normalized_to_utc():
    parsed = BhuvanLightningProvider._parse_datetime("2026-10-04T12:30:00+05:30")
    assert parsed is not None
    assert parsed.isoformat() == "2026-10-04T07:00:00+00:00"


def test_bhuvan_lightning_result_keeps_real_fields_without_synthetic_values():
    result = BhuvanLightningProvider._normalise_result(
        [(
            "grid",
            [{
                "geometry": {"type": "Point", "coordinates": [77.17, 31.10]},
                "properties": {
                    "flash_count": "25",
                    "flash_density": "0.25",
                    "intensity": "Moderate",
                    "time": "2026-10-04T07:00:00Z",
                }
            }]
        )],
        25.0,
    )
    assert result.strike_count == 25
    assert result.density_per_km2 == 0.25
    assert result.flash_rate_per_min is None
    assert result.strike_intensity == "Moderate"
    assert result.latest_observation_time is not None
    assert result.latest_latitude == 31.10
    assert result.latest_longitude == 77.17
