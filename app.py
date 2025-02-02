"""
    README -- Organization of Callback Functions

    In an effort to compartmentalize our development where possible, all callbacks directly relating
    to pages in our application are in their own files.

    For instance, this file contains the layout logic for the index page of our app-
    this page serves all other paths by providing the searchbar, page routing faculties,
    and data storage objects that the other pages in our app use.

    Having laid out the HTML-like organization of this page, we write the callbacks for this page in
    the neighbor 'app_callbacks.py' file.
"""
from concurrent.futures import process
import pstats
import cProfile
import threading
from db_manager.AugurInterface import AugurInterface
from job_manager.job_manager import JobManager
import dash
from dash import html, dcc
import dash_bootstrap_components as dbc
from dash_bootstrap_templates import load_figure_template
import numpy as np
import sys
import os

import logging

logging.basicConfig(level=logging.DEBUG)

# GLOBAL VARIABLE DECLARATIONS
engine = None
search_input = None
all_entries = None
entries = None
augur_db = None
jm = JobManager()


def _load_config():
    global engine
    global augur_db
    # Get config details
    augur_db = AugurInterface()
    engine = augur_db.get_engine()
    if engine is None:
        logging.critical("Could not get engine; check config or try later")
        sys.exit(1)


def _project_list_query():
    global entries
    global all_entries
    global search_input
    global augur_db

    # query of available orgs / repos
    logging.debug("AUGUR_ENTRY_LIST - START")
    pr_query = f"""SELECT * FROM augur_data.explorer_entry_list"""

    df_search_bar = augur_db.run_query(pr_query)

    entries = np.concatenate((df_search_bar.rg_name.unique(), df_search_bar.repo_git.unique()), axis=None)
    entries = entries.tolist()
    entries.sort(key=lambda item: (item, len(item)))

    lower_entries = [i.lower() for i in entries]
    all_entries = list(zip(lower_entries, entries))

    search_input = entries[0]

    logging.debug("AUGUR_ENTRY_LIST - END")


# RUN SETUP FUNCTIONS DEFINED ABOVE
_load_config()
_project_list_query()

# can import this file once we've loaded relevant global variables.
import app_callbacks


# CREATE APP OBJECT
load_figure_template(["sandstone", "minty"])
app = dash.Dash(
    __name__, use_pages=True, external_stylesheets=[dbc.themes.SANDSTONE], suppress_callback_exceptions=True
)

# expose the server variable so that gunicorn can use it.
server = app.server

# side bar code for page navigation
sidebar = html.Div(
    [
        html.H2("Pages", className="display-10"),
        html.Hr(),
        dbc.Nav(
            [
                dbc.NavLink(page["name"], href=page["path"])
                for page in dash.page_registry.values()
                if page["module"] != "pages.not_found_404"
            ],
            vertical=True,
            pills=True,
        ),
    ]
)

# summary layout of the page
app.layout = dbc.Container(
    [
        # componets to store data from queries
        dcc.Store(id="repo-choices", storage_type="session", data=[]),
        dcc.Location(id="url"),
        dbc.Row(
            [
                # from above definition
                dbc.Col(sidebar, width=1),
                dbc.Col(
                    [
                        html.H1("Sandiego Explorer Demo Multipage", className="text-center"),
                        # search bar with buttons
                        html.Label(
                            ["Select Github repos or orgs:"],
                            style={"font-weight": "bold"},
                        ),
                        html.Div(
                            [
                                html.Div(
                                    [
                                        dcc.Dropdown(
                                            id="projects",
                                            multi=True,
                                            options=[search_input],
                                            value=[search_input],
                                        ),
                                        dbc.Alert(
                                            children='Please ensure that your spelling is correct. \
                                                If your selection definitely isn\'t present, please request that \
                                                it be loaded using the help button "REPO/ORG Request" \
                                                in the bottom right corner of the screen.',
                                            id="help-alert",
                                            dismissable=True,
                                            fade=True,
                                            is_open=False,
                                            color="info",
                                        ),
                                    ],
                                    style={
                                        "width": "50%",
                                        "display": "table-cell",
                                        "verticalAlign": "middle",
                                        "padding-right": "10px",
                                    },
                                ),
                                dbc.Button(
                                    "Search",
                                    id="search",
                                    n_clicks=0,
                                    class_name="btn btn-primary",
                                    style={
                                        "verticalAlign": "top",
                                        "display": "table-cell",
                                    },
                                ),
                                dbc.Button(
                                    "Help",
                                    id="search-help",
                                    n_clicks=0,
                                    class_name="btn btn-light",
                                    style={
                                        "verticalAlign": "top",
                                        "display": "table-cell",
                                    },
                                ),
                            ],
                            style={
                                "align": "right",
                                "display": "table",
                                "width": "60%",
                            },
                        ),
                        dcc.Loading(
                            children=[html.Div(id="results-output-container", className="mb-4")],
                            color="#119DFF",
                            type="dot",
                            fullscreen=True,
                        ),
                        # where our page will be rendered
                        dash.page_container,
                    ],
                    width={"size": 11},
                ),
            ],
            justify="start",
        ),
        dbc.Row(
            [
                dbc.Col(
                    [
                        html.H5(
                            "Have a bug or feature request?",
                            className="mb-2"
                            # style={"textDecoration": "underline"},
                        ),
                        html.Div(
                            [
                                dbc.Button(
                                    "Visualization request",
                                    color="primary",
                                    className="me-1",
                                    external_link=True,
                                    target="_blank",
                                    href="https://github.com/sandiego-rh/explorer/issues/new?assignees=&labels=enhancement%2Cvisualization&template=visualizations.md",
                                ),
                                dbc.Button(
                                    "Bug",
                                    color="primary",
                                    className="me-1",
                                    external_link=True,
                                    target="_blank",
                                    href="https://github.com/sandiego-rh/explorer/issues/new?assignees=&labels=bug&template=bug_report.md",
                                ),
                                dbc.Button(
                                    "Repo/Org Request",
                                    color="primary",
                                    external_link=True,
                                    target="_blank",
                                    href="https://github.com/sandiego-rh/explorer/issues/new?assignees=&labels=augur&template=augur_load.md",
                                ),
                            ]
                        ),
                    ],
                    width={"offset": 10},
                )
            ],
        ),
    ],
    fluid=True,
    className="dbc",
    style={"padding-top": "1em"},
)


def main():
    # shouldn't run server in debug mode if we're in a production setting
    debug_mode = True
    try:
        if os.environ["running_on"] == "prod":
            debug_mode = False
        else:
            debug_mode = True
    except:
        debug_mode = True

    app.run(host="0.0.0.0", port=8050, debug=False, process=4, threading=False)


if __name__ == "__main__":

    try:
        if os.environ["profiling"] == "True":
            """
            Ref for how to do this:
            https://www.youtube.com/watch?v=dmnA3axZ3FY

            Credit to IDG TECHTALK
            """
            logging.debug("Profiling")

            cProfile.run("main()", "output.dat")

            with open("output_time.txt", "w") as f:
                p = pstats.Stats("output.dat", stream=f)
                p.sort_stats("time").print_stats()

            with open("output_calls.txt", "w") as f:
                p = pstats.Stats("output.dat", stream=f)
                p.sort_stats("calls").print_stats()
    except KeyError:
        logging.debug("---------PROFILING OFF---------")
        main()
