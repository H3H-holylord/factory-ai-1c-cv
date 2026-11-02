from pathlib import Path
from PIL import Image
from src.demo_renderer import generate_cv_monitoring_image, generate_dashboard_1c_image


def test_generate_demo_images_creates_valid_high_res_pngs(tmp_path: Path):
    cv_path = tmp_path / "demo_cv_monitoring.png"
    dash_path = tmp_path / "demo_dashboard_1c.png"

    generate_cv_monitoring_image(cv_path)
    generate_dashboard_1c_image(dash_path)

    assert cv_path.exists() and cv_path.stat().st_size > 30_000
    assert dash_path.exists() and dash_path.stat().st_size > 30_000

    with Image.open(cv_path) as img_cv:
        assert img_cv.size == (1600, 900)

    with Image.open(dash_path) as img_dash:
        assert img_dash.size == (1600, 950)
