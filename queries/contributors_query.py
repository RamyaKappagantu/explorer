import logging
import pandas as pd
from db_manager.AugurInterface import AugurInterface


def contributors_query(dbmc, repo_ids):
    """
    Worker query

    From an input list of repos, get relevant data about the
    contributions history of those repos. Cache as dictionary in Redis.

    Expects dbm to be db_manager/AugurInterface.
    """
    logging.debug("CONTRIBUTIONS_DATA_QUERY - START")
    repo_statement = str(repo_ids)
    repo_statement = repo_statement[1:-1]

    query_string = f"""
                    SELECT
                        *
                    FROM
                        augur_data.explorer_contributor_actions
                    WHERE
                        repo_id in({repo_statement})
                """

    # create database connection, load config, execute query above.
    dbm = AugurInterface()
    dbm.load_pconfig(dbmc)
    df_cont = dbm.run_query(query_string)

    # update column values
    df_cont.loc[df_cont["action"] == "open_pull_request", "action"] = "Open PR"
    df_cont.loc[df_cont["action"] == "pull_request_comment", "action"] = "PR Comment"
    df_cont.loc[df_cont["action"] == "issue_opened", "action"] = "Issue Opened"
    df_cont.loc[df_cont["action"] == "issue_closed", "action"] = "Issue Closed"
    df_cont.loc[df_cont["action"] == "commit", "action"] = "Commit"
    df_cont.rename(columns={"action": "Action"}, inplace=True)

    df_cont = df_cont.reset_index()
    df_cont.drop("index", axis=1, inplace=True)
    logging.debug("CONTRIBUTIONS_DATA_QUERY - END")
    return df_cont.to_dict("records")
