from dash import html, dcc
import dash
import dash_bootstrap_components as dbc
from dash import callback
from dash.dependencies import Input, Output, State
import plotly.graph_objects as go
import pandas as pd
import datetime as dt
import logging
import plotly.express as px
from pages.utils.graph_utils import get_graph_time_values

from pages.utils.job_utils import handle_job_state, nodata_graph
from queries.commits_query import commits_query as cmq
from app import jm
import time

gc_commits_over_time = dbc.Card(
    [
        dbc.CardBody(
            [
                dcc.Interval(
                    id="commits-over-time-timer",
                    disabled=False,
                    n_intervals=1,
                    max_intervals=1,
                    interval=800,
                ),
                html.H4(
                    "Commits Over Time",
                    className="card-title",
                    style={"text-align": "center"},
                ),
                dbc.Popover(
                    [
                        dbc.PopoverHeader("Graph Info:"),
                        dbc.PopoverBody("Information on overview graph 2"),
                    ],
                    id="overview-popover-2",
                    target="overview-popover-target-2",  # needs to be the same as dbc.Button id
                    placement="top",
                    is_open=False,
                ),
                dcc.Loading(
                    children=[
                        dcc.Graph(
                            id="commits-over-time",
                        )
                    ],
                    color="#119DFF",
                    type="dot",
                    fullscreen=False,
                ),
                dbc.Form(
                    [
                        dbc.Row(
                            [
                                dbc.Label(
                                    "Date Interval:",
                                    html_for="commits-time-interval",
                                    width="auto",
                                    style={"font-weight": "bold"},
                                ),
                                dbc.Col(
                                    dbc.RadioItems(
                                        id="commits-time-interval",
                                        options=[
                                            {
                                                "label": "Day",
                                                "value": 86400000,
                                            },  # days in milliseconds for ploty use
                                            {
                                                "label": "Week",
                                                "value": 604800000,
                                            },  # weeks in milliseconds for ploty use
                                            {"label": "Month", "value": "M1"},
                                            {"label": "Year", "value": "M12"},
                                        ],
                                        value="M1",
                                        inline=True,
                                    ),
                                    className="me-2",
                                ),
                                dbc.Col(
                                    dbc.Button(
                                        "About Graph",
                                        id="overview-popover-target-2",
                                        color="secondary",
                                        size="sm",
                                    ),
                                    width="auto",
                                    style={"padding-top": ".5em"},
                                ),
                            ],
                            align="center",
                        ),
                    ]
                ),
            ]
        ),
    ],
    color="light",
)

# call backs for card graph 2 - Commits Over Time
@callback(
    Output("overview-popover-2", "is_open"),
    [Input("overview-popover-target-2", "n_clicks")],
    [State("overview-popover-2", "is_open")],
)
def toggle_popover_2(n, is_open):
    if n:
        return not is_open
    return is_open


# callback for commits over time graph
@callback(
    Output("commits-over-time", "figure"),
    Output("commits-over-time-timer", "n_intervals"),
    [
        Input("repo-choices", "data"),
        Input("commits-over-time-timer", "n_intervals"),
        Input("commits-time-interval", "value"),
    ],
)
def create_commits_over_time_graph(repolist, timer_pings, interval):
    logging.debug("COMMITS_OVER_TIME_VIZ - START")

    ready, results, graph_update, interval_update = handle_job_state(jm, cmq, repolist)
    if not ready:
        # set n_intervals to 0 so it'll fire again.
        return graph_update, interval_update

    start = time.perf_counter()

    df_commits = pd.DataFrame(results)

    # reset index to be ready for plotly
    df_commits = df_commits.reset_index()

    # time values for graph
    x_r, x_name, hover, period = get_graph_time_values(interval)

    # graph geration
    if df_commits is not None:
        fig = px.histogram(df_commits, x="date", range_x=x_r, labels={"x": x_name, "y": "Commits"})
        fig.update_traces(xbins_size=interval, hovertemplate=hover + "<br>Commits: %{y}<br>")
        fig.update_xaxes(
            showgrid=True,
            ticklabelmode="period",
            dtick=interval,
            rangeslider_yaxis_rangemode="match",
        )
        fig.update_layout(
            xaxis_title=x_name,
            yaxis_title="Number of Commits",
            margin_b=40,
            margin_r=20,
        )
        logging.debug(f"COMMITS_OVER_TIME_VIZ - END - {time.perf_counter() - start}")
        return fig, dash.no_update
    else:
        return nodata_graph, True
