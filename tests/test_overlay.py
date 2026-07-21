from pathlib import Path

from streamlit.testing.v1 import AppTest


def test_results_overlay_renders_without_exception():
    app_path = Path(__file__).resolve().parents[1] / "app.py"
    app = AppTest.from_file(str(app_path), default_timeout=30)
    app.run()
    assert not app.exception
    assert len(app.toggle) == 1

    app.toggle[0].set_value(True).run()
    assert not app.exception
