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


def test_bhuvan_lightning_text_key_value_parser():
    features = BhuvanLightningProvider._text_features(
        "flash_count: 12\nflash_density: 0.12\ncurrent: 18000"
    )
    assert features[0]["properties"]["flash_count"] == "12"
    assert features[0]["properties"]["flash_density"] == "0.12"
    assert features[0]["properties"]["current"] == "18000"


def test_bhuvan_lightning_html_key_value_parser():
    features = BhuvanLightningProvider._html_features(
        "<table><tr><th>flash_count</th><td>12</td></tr>"
        "<tr><th>current</th><td>18000</td></tr></table>"
    )
    assert features[0]["properties"]["flash_count"] == "12"
    assert features[0]["properties"]["current"] == "18000"


def test_bhuvan_lightning_geometry_only_response_is_not_usable():
    gml = """<?xml version="1.0" encoding="UTF-8"?>
    <msGMLOutput xmlns:gml="http://www.opengis.net/gml">
      <grid_layer><gml:name>Bhuvan</gml:name>
        <grid_feature>
          <gml:boundedBy><gml:Box srsName="EPSG:4326">
            <gml:coordinates>88.6,27.3 88.7,27.4</gml:coordinates>
          </gml:Box></gml:boundedBy>
        </grid_feature>
      </grid_layer>
    </msGMLOutput>"""
    assert BhuvanLightningProvider._xml_features(gml) == []


def test_bhuvan_lightning_empty_measurement_is_rejected():
    import pytest

    with pytest.raises(RuntimeError, match="no usable measurement"):
        BhuvanLightningProvider._normalise_result(
            [("grid", [{"properties": {}}])],
            25.0,
        )
