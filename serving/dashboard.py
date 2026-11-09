import logging
from pathlib import Path
import matplotlib.pyplot as plt
from ingestion.raw import to_rows
from processing.extract_transforme import extract
from processing.geo_location import get_country
from serving.aggregate import failed_by_country, success_by_user, failed_invalid_user
from storage.country_cache import load_cache, save_cache, cached_country

"""
    in: three tables from serving.aggregate
    out: one figure with 3 bar charts, saved as dashboard.png and shown on screen
         - failed attempts per country
         - successful attempts per user
         - failed attempts with invalid user (per username)
"""

logger = logging.getLogger(__name__)
logger.setLevel(logging.WARNING)
logger_format = logging.Formatter(
    fmt='%(asctime)s|%(levelname)s|%(name)s|%(message)s',
    datefmt='%d-%b-%Y %H:%M:%S %p'
)
console = logging.StreamHandler()
console.setFormatter(logger_format)
logger.addHandler(console)
file = logging.FileHandler(Path(__file__).parent / 'dashboard.log')
file.setFormatter(logger_format)
logger.addHandler(file)

TOP = 10    #bars per chart

def top_n(table, n=TOP):
    return dict(list(table.items())[:n])

def bar_chart(ax, table, title, xlabel, color):
    """horizontal bar chart on one axis, biggest bar on top"""
    ax.set_title(title)
    if not table:
        logger.warning('No data for chart: %s', title)
        ax.text(0.5, 0.5, 'No data', ha='center', va='center', transform=ax.transAxes)
        return
    labels = list(table.keys())
    values = list(table.values())
    ax.barh(labels, values, color=color, height=0.6)
    ax.set_ylim(max(len(values), 5) - 0.5, -0.5)   
    ax.set_xlabel(xlabel)
    for i, value in enumerate(values):
        ax.text(value,i,f'{value}',va='center')
    ax.margins(x=0.15)     
    if max(values) <= 10:   # small counts: whole numbers only on the axis
        ax.set_xticks(range(0, max(values) + 2))


def build_dashboard(by_country, by_user, invalid_user, save_path=None, show=True):
    fig, axes = plt.subplots(1, 3, figsize=(20, 6))
    bar_chart(axes[0], top_n(by_country), f'Failed attempts per country (top {TOP})',
              'failed attempts', 'tab:red')
    bar_chart(axes[1], top_n(by_user), 'Successful attempts per user',
              'successful attempts', 'tab:green')
    bar_chart(axes[2], top_n(invalid_user), f'Failed attempts with invalid user (top {TOP})',
              'failed attempts', 'tab:orange')
    fig.suptitle('SSH authentication dashboard')
    fig.tight_layout()
    if save_path:
        try:
            fig.savefig(save_path)
        except Exception as e:
            logger.error('Cannot save dashboard to %s: %s', save_path, e)
    if show:
        plt.show()
    return fig


if __name__ == '__main__':

    events = extract(to_rows('./data'))
    cache = load_cache()
    try:
        by_country = failed_by_country(events, lambda ip: cached_country(ip, cache, get_country))
    finally:
        save_cache(cache)       # also runs if you press Ctrl+C
    by_user = success_by_user(events)
    invalid_user = failed_invalid_user(events)
    build_dashboard(by_country, by_user, invalid_user,save_path=Path(__file__).parent / 'dashboard.png')