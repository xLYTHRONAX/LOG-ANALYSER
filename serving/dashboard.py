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


TOP = 10    # bars per chart

# Color palette
BG = '#d4d4d4'        
TEXT = '#1f1f1f'      
GREY = '#707070'      
DEEP_RED = '#731010'  
RED = '#a80000'      


def top_n(table, n=TOP):
    """first n items of a table (tables are already sorted, biggest first)"""
    return dict(list(table.items())[:n])


def bar_chart(ax, table, title, xlabel, color, highlight=None):
    """
    horizontal bar chart on one axis, biggest bar on top.
    color: color of the bars, highlight: color of the biggest bar (same as color if None)
    """
    ax.set_facecolor(BG)
    ax.set_title(title, color=RED, fontsize=14, fontweight='bold', loc='left', pad=14)
    for side in ('top', 'right'):
        ax.spines[side].set_visible(False)
    for side in ('left', 'bottom'):
        ax.spines[side].set_color(GREY)
    ax.tick_params(colors=TEXT, length=0, labelsize=11)
    ax.set_xlabel(xlabel, color=GREY, fontsize=10)
    ax.set_axisbelow(True)
    ax.grid(axis='x', color=GREY, alpha=0.3, linewidth=0.8)

    if not table:
        logger.warning('No data for chart: %s', title)
        ax.text(0.5, 0.5, 'No data', ha='center', va='center', color=GREY,
                fontsize=14, transform=ax.transAxes)
        return
    labels = list(table.keys())
    values = list(table.values())
    colors = [highlight or color] + [color] * (len(values) - 1)
    ax.barh(labels, values, color=colors, height=0.65)
    ax.set_ylim(max(len(values), 5) - 0.5, -0.5)   # biggest on top, slim bars when few items
    for i, value in enumerate(values):
        ax.text(value, i, f'  {value:,}', va='center', color=TEXT, fontsize=11, fontweight='bold')
    ax.margins(x=0.18)      # room for the numbers
    if max(values) <= 10:   # small counts: whole numbers only on the axis
        ax.set_xticks(range(0, max(values) + 2))


def build_dashboard(by_country, by_user, invalid_user, save_path=None, show=True):
    fig, axes = plt.subplots(1, 3, figsize=(20, 7.5), facecolor=BG)
    bar_chart(axes[0], top_n(by_country), f'Failed attempts per country (top {TOP})',
              'failed attempts', DEEP_RED, highlight=RED)
    bar_chart(axes[1], top_n(by_user), 'Successful attempts per user',
              'successful attempts', GREY)
    bar_chart(axes[2], top_n(invalid_user), f'Failed attempts with invalid user (top {TOP})',
              'failed attempts', DEEP_RED, highlight=RED)

    # header: title + key numbers computed from the tables
    fig.text(0.03, 0.955, 'SSH AUTHENTICATION DASHBOARD', color=DEEP_RED, fontsize=24,
             fontweight='bold', ha='left', va='center')
    summary = (f'{sum(by_country.values()):,} failed attempts   |   '
               f'{sum(invalid_user.values()):,} with an invalid user   |   '
               f'{sum(by_user.values()):,} successful')
    fig.text(0.03, 0.905, summary, color=GREY, fontsize=13, ha='left', va='center')

    fig.tight_layout(rect=(0.01, 0.01, 0.99, 0.86))
    if save_path:
        try:
            fig.savefig(save_path, dpi=150, facecolor=BG)
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