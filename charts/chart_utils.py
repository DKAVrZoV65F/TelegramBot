# utils/chart_utils.py

from datetime import datetime
import io
import matplotlib

matplotlib.use('Agg')
import matplotlib.pyplot as plt
import matplotlib.dates as mdates


def generate_pie_chart(data: dict, title: str) -> io.BytesIO | None:
    if not data:
        return None

    labels = data.keys()
    sizes = list(data.values())

    def make_auto_pct(values):
        def my_auto_pct(pct):
            if pct is None:
                return ''
            absolute = int(round(pct / 100. * sum(values)))
            return f"{pct:.1f}%\n({absolute})"

        return my_auto_pct

    fig, ax = plt.subplots(figsize=(10, 7))

    colors = plt.cm.Paired.colors

    wedges, texts, auto_texts = ax.pie(
        sizes,
        autopct=make_auto_pct(sizes),
        startangle=90,
        pctdistance=0.80,
        colors=colors[:len(labels)]
    )

    for auto_text in auto_texts:
        auto_text.set_color('white')
        auto_text.set_fontsize(9)
        auto_text.set_fontweight('bold')

    ax.axis('equal')
    plt.title(title, pad=20, fontsize=14)

    ax.legend(wedges, labels,
              title="Легенды",
              loc="center left",
              bbox_to_anchor=(1, 0, 0.5, 1),
              fontsize=10)

    plt.tight_layout(rect=[0, 0, 0.75, 1])

    buf = io.BytesIO()
    plt.savefig(buf, format='png', bbox_inches='tight')
    buf.seek(0)
    plt.close(fig)
    return buf


def generate_line_chart(trends_data: dict, title: str, y_label: str = "Количество упоминаний") -> io.BytesIO | None:
    if not trends_data:
        return None

    fig, ax = plt.subplots(figsize=(12, 7))

    has_data_to_plot = False
    colors = plt.cm.tab10.colors

    tag_index = 0
    for tag_name, data_points in trends_data.items():
        if not data_points:
            continue

        dates_str = [dp[0] for dp in data_points]
        counts = [dp[1] for dp in data_points]

        dates_dt = [datetime.strptime(d_str, "%Y-%m-%d").date() for d_str in dates_str]

        if not any(c > 0 for c in counts):
            continue

        ax.plot(dates_dt, counts, marker='o', linestyle='-', label=tag_name, color=colors[tag_index % len(colors)])
        has_data_to_plot = True
        tag_index += 1

    if not has_data_to_plot:
        plt.close(fig)
        return None

    ax.set_title(title, fontsize=15, pad=20)
    ax.set_xlabel("Дата", fontsize=12)
    ax.set_ylabel(y_label, fontsize=12)

    ax.xaxis.set_major_formatter(mdates.DateFormatter('%Y-%m-%d'))
    ax.xaxis.set_minor_locator(mdates.DayLocator())
    plt.xticks(rotation=45, ha="right")

    ax.grid(True, linestyle='--', alpha=0.7)
    ax.legend(loc="center left", bbox_to_anchor=(1, 0.5))

    plt.tight_layout(rect=[0, 0, 0.80, 1])

    buf = io.BytesIO()
    plt.savefig(buf, format='png', bbox_inches='tight')
    buf.seek(0)
    plt.close(fig)
    return buf
