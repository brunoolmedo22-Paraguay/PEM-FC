import numpy as np

from models.pemfc_model import PEMFCModel
from pemfc_config.parameters import DEFAULT_PARAMS


def test_default_stack_has_41_cells():
    assert DEFAULT_PARAMS.N_cells == 41


def test_current_conversion_at_one_amp_per_square_centimeter():
    model = PEMFCModel()
    assert np.isclose(model.total_current([1.0])[0], 232.0)


def test_voltage_near_published_values_at_one_amp_per_square_centimeter():
    model = PEMFCModel()
    v298 = model.cell_voltage([1.0], 298.15, 5.0)[0]
    v373 = model.cell_voltage([1.0], 373.15, 5.0)[0]
    assert 0.50 <= v298 <= 0.57
    assert 0.55 <= v373 <= 0.60


def test_stack_power_is_kilowatt_scale_not_single_cell_scale():
    model = PEMFCModel()
    p298 = model.stack_power([1.0], 298.15, 5.0)[0]
    p373 = model.stack_power([1.0], 373.15, 5.0)[0]
    assert 4800 <= p298 <= 5400
    assert 5200 <= p373 <= 5700
    assert p298 > 1000  # falha explicitamente se voltar ao resultado ~140 W


def test_efficiency_near_figure3_at_one_amp_per_square_centimeter():
    model = PEMFCModel()
    eta298 = model.efficiency_percent([1.0], 298.15, 5.0)[0]
    eta373 = model.efficiency_percent([1.0], 373.15, 5.0)[0]
    assert 28.5 <= eta298 <= 31.5
    assert 31.0 <= eta373 <= 34.0


def test_pressure_effect_has_correct_direction():
    model = PEMFCModel()
    T = model.params.pressure_temperature_K
    v1 = model.cell_voltage([0.6], T, 1.0)[0]
    v5 = model.cell_voltage([0.6], T, 5.0)[0]
    assert v5 > v1
    assert 0.0 < v5 - v1 < 0.03


def test_outputs_are_finite_and_physical():
    model = PEMFCModel()
    j = np.linspace(0, 1, 201)
    for T in (298.15, 373.15):
        df = model.evaluate(j, T, 5.0)
        assert np.isfinite(df.select_dtypes(include=[float, int]).to_numpy()).all()
        assert (df.V_cell_V >= 0).all()
        assert (df.V_cell_V <= 1.3).all()
        assert (df.P_stack_W >= 0).all()


def test_figure3_generation_does_not_require_digitized_csvs():
    model = PEMFCModel()
    data = model.figure3_data()
    assert set(data) == {"T_298", "T_373", "P_1", "P_5"}
    assert all(len(frame) > 100 for frame in data.values())
