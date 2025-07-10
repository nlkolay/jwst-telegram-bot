import logging
import numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib.patches import Ellipse, Arc
from astropy.time import Time
from astroquery.jplhorizons import Horizons
import astropy.units as u
import os
import uuid
from requests.exceptions import HTTPError

logger = logging.getLogger(__name__)

REQUEST_TIMEOUT = 10 # seconds

ASSETS_DIR = os.path.join(os.path.dirname(__file__), '..', 'assets')
if not os.path.exists(ASSETS_DIR):
    os.makedirs(ASSETS_DIR)

# Константа для перевода а.е. в тысячи км
AU_TO_THOUSAND_KM = 149597.8707

def create_position_image(positions: dict) -> str | None:
    """
    Создает изображение, показывающее положение Земли, Луны и JWST.
    """
    try:
        plt.style.use('dark_background')
        fig, ax = plt.subplots(figsize=(12, 12))
        fig.patch.set_facecolor('#0d1117')
        ax.set_facecolor('#0d1117')

        # --- Конвертация в тыс. км ---
        positions_km = {name: {
            'x': pos['x'] * AU_TO_THOUSAND_KM,
            'y': pos['y'] * AU_TO_THOUSAND_KM
        } for name, pos in positions.items()}

        # --- Объекты ---
        # Земля в центре
        ax.plot(0, 0, 'o', markersize=10, color='deepskyblue', label='Земля')

        # Луна
        if 'moon' in positions_km:
            moon_x_km, moon_y_km = positions_km['moon']['x'], positions_km['moon']['y']
            ax.plot(moon_x_km, moon_y_km, 'o', markersize=6, color='silver', label='Луна')
            # Орбита Луны
            moon_orbit_radius_km = np.sqrt(moon_x_km**2 + moon_y_km**2)
            moon_orbit = plt.Circle((0, 0), moon_orbit_radius_km, color='gray', linestyle='--', fill=False, linewidth=0.8)
            ax.add_artist(moon_orbit)

        # Орбита Земли (сегмент)
        earth_orbit_radius_km = 149600 # тыс. км
        earth_orbit_arc = Arc((0 - earth_orbit_radius_km, 0),
                              earth_orbit_radius_km * 2, earth_orbit_radius_km * 2,
                              theta1=-1, theta2=1, color='darkgoldenrod', linestyle='-.', linewidth=1, label='Орбита Земли (сегмент)')
        ax.add_artist(earth_orbit_arc)

        # --- Орбита и положение JWST ---
        # 1. Определяем точку L2 (упрощенно, на оси X)
        l2_distance_km = 1500 # тыс. км от Земли
        l2_point = np.array([-l2_distance_km, 0])
        ax.text(l2_point[0], l2_point[1] + 50, 'L2', color='cyan', ha='center', fontsize=10)

        # 2. Рисуем большую, более реалистичную орбиту-гало вокруг L2
        orbit_width = 800  # тыс. км
        orbit_height = 1300 # тыс. км
        orbit_angle_deg = 15 # Наклон для псевдо-3D вида
        jwst_orbit = Ellipse(xy=l2_point, width=orbit_width, height=orbit_height,
                               angle=orbit_angle_deg, edgecolor='cyan', fc='none', ls=':', lw=1.5)
        ax.add_artist(jwst_orbit)

        # 3. "Примагничиваем" JWST к нарисованной орбите для наглядности
        if 'jwst' not in positions_km or not positions_km['jwst'] or not positions_km['jwst']['x'] or not positions_km['jwst']['y']:
            logger.error("Отсутствуют или неверны координаты для JWST.")
            return None
        jwst_pos_actual = np.array([positions_km['jwst']['x'], positions_km['jwst']['y'] ])
        # Вектор от L2 к реальному положению JWST
        vec_l2_to_jwst = jwst_pos_actual - l2_point
        # Угол этого вектора
        angle_rad = np.arctan2(vec_l2_to_jwst[1], vec_l2_to_jwst[0])

        # 4. Находим точку на эллипсе, соответствующую этому углу
        # Учитываем поворот эллипса
        cos_a = np.cos(np.radians(orbit_angle_deg))
        sin_a = np.sin(np.radians(orbit_angle_deg))
        cos_b = np.cos(angle_rad)
        sin_b = np.sin(angle_rad)

        # Параметрическое уравнение эллипса
        t = np.arctan2(sin_b / (orbit_height/2), cos_b / (orbit_width/2))
        x_on_ellipse = (orbit_width/2) * np.cos(t)
        y_on_ellipse = (orbit_height/2) * np.sin(t)

        # Поворачиваем точку вместе с эллипсом
        x_rotated = x_on_ellipse * cos_a - y_on_ellipse * sin_a
        y_rotated = x_on_ellipse * sin_a + y_on_ellipse * cos_a

        jwst_x_on_orbit = x_rotated + l2_point[0]
        jwst_y_on_orbit = y_rotated + l2_point[1]

        ax.plot(jwst_x_on_orbit, jwst_y_on_orbit, '* ', markersize=10, color='white', label='Телескоп «Уэбб» (на орбите L2)')

        # --- Настройки ---
        ax.set_aspect('equal', adjustable='box')
        limit_km = 2200 # 2.2 млн км
        ax.set_xlim(-limit_km, limit_km)
        ax.set_ylim(-limit_km, limit_km)

        ax.grid(True, linestyle=':', alpha=0.3)
        ax.set_xlabel("Расстояние от Земли (тыс. км)", fontsize=12)
        ax.set_ylabel("Расстояние от Земли (тыс. км)", fontsize=12)
        plt.title('Положение Луны и телескопа «Уэбб» относительно Земли', fontsize=16, pad=20)
        ax.legend(loc='upper left', facecolor='#161b22', edgecolor='gray', fontsize=11)

        # --- Сохранение ---
        filename = f"jwst_position_{uuid.uuid4()}.png"
        filepath = os.path.join(ASSETS_DIR, filename)
        plt.savefig(filepath, bbox_inches='tight', pad_inches=0.2, dpi=150)
        plt.close(fig)

        logger.info(f"Изображение с положением сохранено в: {filepath}")
        return filepath

    except Exception as e:
        logger.error(f"Ошибка при создании изображения: {e}. Проверьте входные данные и библиотеки для отрисовки.", exc_info=True)
        if 'fig' in locals() and plt.fignum_exists(fig.number):
            plt.close(fig)
        return None

def create_jwst_orbit_plot():
    """
    Создает график орбиты JWST относительно Земли и Луны.

    Returns:
        str: Путь к сохраненному файлу с графиком, "JPL_ERROR" в случае ошибки сети, или None.
    """
    try:
        logger.info("Начинаю получение данных об орбите и генерацию графика...")
        # Время для запроса (текущее время)
        now = Time.now()
        # Для получения положения JWST относительно Земли, нам нужно запросить их оба
        # и затем вычислить относительное положение.
        # JPL Horizons ID для Земли: 399
        # JPL Horizons ID для Луны: 301
        # JPL Horizons ID для JWST: -170 (или 2000000)

        # Получаем данные для Земли (в центре)
        # Earth is the origin (0,0,0) in this plot, so we don't need its ephemeris
        # We need Moon and JWST relative to Earth.

        # Получаем данные для Луны относительно Земли
        obj_moon = Horizons(id='301', location='399', epochs=now.jd, id_type='majorbody')
        eph_moon = obj_moon.vectors(refplane='ecliptic')

        # Получаем данные для JWST относительно Земли
        obj_jwst = Horizons(id='-170', location='399', epochs=now.jd, id_type='id')
        eph_jwst = obj_jwst.vectors(refplane='ecliptic')

        positions = {
            'earth': {'x': 0, 'y': 0},
            'moon': {'x': eph_moon['x'][0], 'y': eph_moon['y'][0]},
            'jwst': {'x': eph_jwst['x'][0], 'y': eph_jwst['y'][0]}
        }

        plot_path = create_position_image(positions)
        return plot_path

    except HTTPError as e:
        logger.error(f"Ошибка сети при запросе к JPL Horizons: {e}", exc_info=True)
        return "JPL_ERROR"
    except Exception as e:
        logger.error(f"Неизвестная ошибка при создании графика орбиты JWST: {e}", exc_info=True)
        return None