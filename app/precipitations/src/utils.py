import matplotlib.pyplot as plt
import matplotlib.dates as mdates
import numpy


# Function to adjust the alignment of two y axis
def align_yaxis(ax, ax2):
    y_lims = numpy.array([ax.get_ylim() for ax in [ax, ax2]])

    # Normalize both y axis
    y_magnitudes = (y_lims[:, 1] - y_lims[:, 0]).reshape(len(y_lims), 1)
    y_lims_normalized = y_lims / y_magnitudes

    # Find combined range
    y_new_lims_normalized = numpy.array(
        [numpy.min(y_lims_normalized), numpy.max(y_lims_normalized)]
    )

    # Denormalize combined range to get new axis
    new_lim1, new_lim2 = y_new_lims_normalized * y_magnitudes
    ax2.set_ylim(new_lim2)


# Function to create the plot
def fig(x, y, title, xlabel, ylabel, ylim, color="black", y2="", y2label=""):
    # Plot and text size parameters
    params = {
        "legend.fontsize": "14",
        "figure.figsize": (8, 6),
        "axes.labelsize": "14",
        "axes.titlesize": "16",
        "xtick.labelsize": "12",
        "ytick.labelsize": "12",
    }
    plt.rcParams.update(params)

    # Plot creation and plot styling
    fig, ax = plt.subplots()
    ax.plot(x, y, marker="o")

    # Titles
    plt.title(title)
    plt.xlabel(xlabel)
    ax.set_ylabel(ylabel, color=color)

    # Y axis range
    ax.set_ylim(ylim)
    ax.tick_params(axis="y", labelcolor=color)

    # Grid
    plt.grid(True, which="both")

    # Add a second dataset
    if y2 is not None:
        ax2 = plt.twinx()
        ax2.plot(x, y2, marker="o", color="tab:red")
        # Second y axis title
        ax2.set_ylabel(y2label, color="tab:red")
        # Range and ticks of second y axis
        ax2.set_ylim(0, (max(y2) * 1.1))
        ax2.tick_params(axis="y", labelcolor="tab:red")
        align_yaxis(ax, ax2)

    # Date format on x axis
    plt.gcf().autofmt_xdate()
    my_format = mdates.DateFormatter("%m/%d %H:%M")
    plt.gca().xaxis.set_major_formatter(my_format)

    # Graduation of x axis depending on the number of values plotted
    # Variable containing the hours for which there will be ticks:
    hour = []
    for timestep in x:
        hour.append(int(timestep.strftime("%H")))

    # Frequency of ticks and labels on the x axis
    if len(hour) < 8:
        # More precise graduation if there is only a few values plotted
        ax.xaxis.set_major_locator(mdates.HourLocator(byhour=hour))
    elif len(hour) > 8 and len(hour) < 25:
        ax.xaxis.set_major_locator(mdates.HourLocator(byhour=hour, interval=2))
        ax.xaxis.set_minor_locator(mdates.HourLocator(byhour=hour))
    else:
        # Coarser graduation if there is a lot of values plotted
        ax.xaxis.set_major_locator(mdates.DayLocator())
        ax.xaxis.set_minor_locator(mdates.HourLocator(byhour=(0, 12)))

    return fig
