import numpy as np
import pandas as pd


def batting_summary(
    df,
    # Existing value filters
    player_name=None,
    pid=None,
    inns=None,
    mat_num=None,
    team_bat=None,
    team_bowl=None,
    bowler_name=None,
    competition=None,
    date_from=None,
    date_to=None,
    over_values=None,
    phase=None,
    bowler_id=None,
    ground=None,
    mcode=None,
    bat_hand=None,
    bowl_type=None,
    bowl_kind=None,
    bowl_arm=None,
    # Additional requested filters
    year_from=None,
    year_to=None,
    min_balls=None,
    # Placeholder filters (kept intentionally inactive for now)
    batting_position=None,
    nationality=None,
    age_range=None,
    # Metric config
    sr10_balls=10,
):
    local_df = df.copy()

    # --------- Value filters (same style as spike plot) ---------
    if pid is not None:
        local_df = local_df[local_df["p_bat"].astype(str) == str(pid)]
        if not local_df.empty and player_name is None:
            player_name = local_df["bat"].iloc[0]
    elif player_name is not None:
        if isinstance(player_name, (list, tuple, set)):
            local_df = local_df[local_df["bat"].isin(list(player_name))]
        else:
            local_df = local_df[local_df["bat"] == player_name]

    if mat_num is not None:
        if isinstance(mat_num, (list, tuple, set)):
            local_df = local_df[local_df["p_match"].isin(list(mat_num))]
        else:
            local_df = local_df[local_df["p_match"] == mat_num]

    if inns is not None:
        if isinstance(inns, (list, tuple, set)):
            if len(inns) > 0:
                local_df = local_df[local_df["inns"].isin(list(inns))]
        else:
            local_df = local_df[local_df["inns"] == inns]

    if team_bat is not None:
        if isinstance(team_bat, (list, tuple, set)):
            if len(team_bat) > 0:
                local_df = local_df[local_df["team_bat"].isin(list(team_bat))]
        else:
            local_df = local_df[local_df["team_bat"] == team_bat]

    if team_bowl is not None:
        if isinstance(team_bowl, (list, tuple, set)):
            if len(team_bowl) > 0:
                local_df = local_df[local_df["team_bowl"].isin(list(team_bowl))]
        else:
            local_df = local_df[local_df["team_bowl"] == team_bowl]

    if competition:
        local_df = local_df[local_df["competition"] == competition]

    if over_values is not None:
        if isinstance(over_values, (list, tuple, set)):
            local_df = local_df[local_df["over"].isin(list(over_values))]
        else:
            local_df = local_df[local_df["over"] == over_values]

    # Phase logic exactly as discussed
    if phase is not None:
        phase_list = list(phase) if isinstance(phase, (list, tuple, set)) else [phase]
        if len(phase_list) > 0:
            mask = pd.Series([False] * len(local_df), index=local_df.index)
            if 1 in phase_list:
                mask |= local_df["over"].between(1, 6)
            if 2 in phase_list:
                mask |= local_df["over"].between(7, 15)
            if 3 in phase_list:
                mask |= local_df["over"].between(16, 20)
            local_df = local_df[mask]

    if date_from is not None:
        local_df = local_df[local_df["date"] >= pd.to_datetime(date_from)]

    if date_to is not None:
        local_df = local_df[local_df["date"] <= pd.to_datetime(date_to)]

    if ground is not None:
        if isinstance(ground, (list, tuple, set)):
            if len(ground) > 0:
                local_df = local_df[local_df["ground"].isin(list(ground))]
        else:
            local_df = local_df[local_df["ground"] == ground]

    if mcode is not None:
        if isinstance(mcode, (list, tuple, set)):
            if len(mcode) > 0:
                local_df = local_df[local_df["mcode"].isin(list(mcode))]
        else:
            local_df = local_df[local_df["mcode"] == mcode]

    if bat_hand is not None:
        if isinstance(bat_hand, (list, tuple, set)):
            if len(bat_hand) > 0:
                local_df = local_df[local_df["bat_hand"].isin(list(bat_hand))]
        else:
            local_df = local_df[local_df["bat_hand"] == bat_hand]

    if bowl_type is not None:
        if isinstance(bowl_type, (list, tuple, set)):
            if len(bowl_type) > 0:
                local_df = local_df[local_df["bowl_type"].isin(list(bowl_type))]
        else:
            local_df = local_df[local_df["bowl_type"] == bowl_type]

    if bowl_kind is not None:
        if isinstance(bowl_kind, (list, tuple, set)):
            if len(bowl_kind) > 0:
                local_df = local_df[local_df["bowl_kind"].isin(list(bowl_kind))]
        else:
            local_df = local_df[local_df["bowl_kind"] == bowl_kind]

    if bowl_arm is not None:
        if isinstance(bowl_arm, (list, tuple, set)):
            if len(bowl_arm) > 0:
                local_df = local_df[local_df["bowl_arm"].isin(list(bowl_arm))]
        else:
            local_df = local_df[local_df["bowl_arm"] == bowl_arm]

    if bowler_id is not None:
        local_df = local_df[local_df["p_bowl"] == bowler_id]
        if not local_df.empty and bowler_name is None:
            bowler_name = local_df["bowl"].iloc[0]
    elif bowler_name is not None:
        if isinstance(bowler_name, (list, tuple, set)):
            local_df = local_df[local_df["bowl"].isin(list(bowler_name))]
        else:
            local_df = local_df[local_df["bowl"] == bowler_name]

    if year_from is not None:
        local_df = local_df[local_df["year"] >= int(year_from)]

    if year_to is not None:
        local_df = local_df[local_df["year"] <= int(year_to)]

    # Placeholder filters (kept intentionally, no-op until engineered columns exist)
    # batting_position
    # nationality
    # age_range

    if local_df.empty:
        return pd.DataFrame(
            columns=[
                "Player", "Balls", "Runs", "HS", "SR", "SR10", "Avg",
                "B/Dis", "B/4", "B/6", "B/Bdy",
                "Bdy%", "BRns%", "NB-SR", "Dot%", "Run%",
                "PP SR", "Mid SR", "Dth SR", "Accel", "30+%",
                "SR-I", "SR-II",
            ]
        )

    # --------- Type normalization ---------
    local_df["wide"] = pd.to_numeric(local_df["wide"], errors="coerce").fillna(0)
    local_df["batruns"] = pd.to_numeric(local_df["batruns"], errors="coerce").fillna(0)
    local_df["ballfaced"] = pd.to_numeric(local_df["ballfaced"], errors="coerce").fillna(0)
    local_df["over"] = pd.to_numeric(local_df["over"], errors="coerce")
    local_df["inns"] = pd.to_numeric(local_df["inns"], errors="coerce")
    local_df["p_match"] = pd.to_numeric(local_df["p_match"], errors="coerce")
    local_df["p_bat"] = pd.to_numeric(local_df["p_bat"], errors="coerce")
    local_df["p_out"] = pd.to_numeric(local_df["p_out"], errors="coerce")
    local_df["out"] = local_df["out"].fillna(False).astype(bool)

    # Legal balls only
    valid_balls = local_df[local_df["wide"] == 0].copy()

    if valid_balls.empty:
        return pd.DataFrame(
            columns=[
                "Player", "Balls", "Runs", "HS", "SR", "SR10", "Avg",
                "B/Dis", "B/4", "B/6", "B/Bdy",
                "Bdy%", "BRns%", "NB-SR", "Dot%", "Run%",
                "PP SR", "Mid SR", "Dth SR", "Accel", "30+%",
                "SR-I", "SR-II",
            ]
        )

    # --------- Core totals ---------
    summary = (
        valid_balls.groupby(["bat", "p_bat"], dropna=False)
        .agg(Balls=("batruns", "size"), Runs=("batruns", "sum"))
        .reset_index()
    )

    innings_totals = (
        valid_balls.groupby(["bat", "p_bat", "p_match", "inns"], dropna=False)["batruns"]
        .sum()
        .reset_index(name="InningsRuns")
    )

    hs = (
        innings_totals.groupby(["bat", "p_bat"], dropna=False)["InningsRuns"]
        .max()
        .reset_index(name="HS")
    )

    dismissals = (
        valid_balls[
            valid_balls["out"]
            & valid_balls["p_out"].notna()
            & (valid_balls["p_out"] == valid_balls["p_bat"])
        ]
        .groupby(["bat", "p_bat"], dropna=False)
        .size()
        .reset_index(name="Dismissals")
    )

    # Four/six validation
    valid_balls["is_four"] = (
        (valid_balls["batruns"] == 4) & (valid_balls["outcome"] == "four")
    ).astype(int)
    valid_balls["is_six"] = (
        (valid_balls["batruns"] == 6) & (valid_balls["outcome"] == "six")
    ).astype(int)

    boundaries = (
        valid_balls.groupby(["bat", "p_bat"], dropna=False)
        .agg(Fours=("is_four", "sum"), Sixes=("is_six", "sum"))
        .reset_index()
    )

    # SR10
    valid_balls = valid_balls.sort_values(
        ["p_match", "inns", "over", "ball", "ball_id"], kind="mergesort"
    )

    first_10 = (
        valid_balls.groupby(["p_match", "inns"], dropna=False, sort=False)
        .head(sr10_balls)
        .copy()
    )

    sr10_df = (
        first_10.groupby(["bat", "p_bat"], dropna=False)
        .agg(SR10_Runs=("batruns", "sum"), SR10_Balls=("batruns", "size"))
        .reset_index()
    )

    # Rate support columns
    valid_balls["is_boundary"] = (
        ((valid_balls["batruns"] == 4) & (valid_balls["outcome"] == "four"))
        | ((valid_balls["batruns"] == 6) & (valid_balls["outcome"] == "six"))
    )
    valid_balls["is_dot"] = (valid_balls["ballfaced"] == 1) & (valid_balls["batruns"] == 0)
    valid_balls["is_run_ball"] = (valid_balls["ballfaced"] == 1) & (valid_balls["batruns"].isin([1, 2, 3]))
    valid_balls["boundary_runs"] = np.where(valid_balls["is_boundary"], valid_balls["batruns"], 0)

    rate_stats = (
        valid_balls.groupby(["bat", "p_bat"], dropna=False)
        .agg(
            BoundaryBalls=("is_boundary", "sum"),
            BoundaryRuns=("boundary_runs", "sum"),
            DotBalls=("is_dot", "sum"),
            RunBalls=("is_run_ball", "sum"),
            RunBallsRuns=("batruns", lambda s: s[s.isin([1, 2, 3])].sum()),
        )
        .reset_index()
    )

    # Phase SRs
    pp_df = (
        valid_balls[valid_balls["over"].between(1, 6)]
        .groupby(["bat", "p_bat"], dropna=False)
        .agg(PP_Runs=("batruns", "sum"), PP_Balls=("batruns", "size"))
        .reset_index()
    )
    mid_df = (
        valid_balls[valid_balls["over"].between(7, 15)]
        .groupby(["bat", "p_bat"], dropna=False)
        .agg(Mid_Runs=("batruns", "sum"), Mid_Balls=("batruns", "size"))
        .reset_index()
    )
    dth_df = (
        valid_balls[valid_balls["over"].between(16, 20)]
        .groupby(["bat", "p_bat"], dropna=False)
        .agg(Dth_Runs=("batruns", "sum"), Dth_Balls=("batruns", "size"))
        .reset_index()
    )

    # SR-I and SR-II
    si_df = (
        valid_balls[valid_balls["inns"] == 1]
        .groupby(["bat", "p_bat"], dropna=False)
        .agg(SR_I_Runs=("batruns", "sum"), SR_I_Balls=("batruns", "size"))
        .reset_index()
    )
    sii_df = (
        valid_balls[valid_balls["inns"] == 2]
        .groupby(["bat", "p_bat"], dropna=False)
        .agg(SR_II_Runs=("batruns", "sum"), SR_II_Balls=("batruns", "size"))
        .reset_index()
    )

    # 30+%
    innings_30_df = (
        innings_totals.assign(Innings30Plus=(innings_totals["InningsRuns"] >= 30).astype(int))
        .groupby(["bat", "p_bat"], dropna=False)
        .agg(InningsCount=("InningsRuns", "size"), Innings30Plus=("Innings30Plus", "sum"))
        .reset_index()
    )

    # Merge all
    summary = summary.merge(hs, on=["bat", "p_bat"], how="left")
    summary = summary.merge(dismissals, on=["bat", "p_bat"], how="left")
    summary = summary.merge(boundaries, on=["bat", "p_bat"], how="left")
    summary = summary.merge(sr10_df, on=["bat", "p_bat"], how="left")
    summary = summary.merge(rate_stats, on=["bat", "p_bat"], how="left")
    summary = summary.merge(pp_df, on=["bat", "p_bat"], how="left")
    summary = summary.merge(mid_df, on=["bat", "p_bat"], how="left")
    summary = summary.merge(dth_df, on=["bat", "p_bat"], how="left")
    summary = summary.merge(si_df, on=["bat", "p_bat"], how="left")
    summary = summary.merge(sii_df, on=["bat", "p_bat"], how="left")
    summary = summary.merge(innings_30_df, on=["bat", "p_bat"], how="left")

    # Fill nulls
    fill_int_cols = [
        "Dismissals", "Fours", "Sixes", "SR10_Balls", "BoundaryBalls",
        "DotBalls", "RunBalls", "InningsCount", "Innings30Plus",
        "PP_Balls", "Mid_Balls", "Dth_Balls", "SR_I_Balls", "SR_II_Balls",
    ]
    fill_run_cols = [
        "SR10_Runs", "BoundaryRuns", "RunBallsRuns",
        "PP_Runs", "Mid_Runs", "Dth_Runs", "SR_I_Runs", "SR_II_Runs",
    ]

    for col in fill_int_cols + fill_run_cols:
        if col in summary.columns:
            summary[col] = summary[col].fillna(0)

    for col in fill_int_cols:
        if col in summary.columns:
            summary[col] = summary[col].astype(int)

    # --------- Metrics ---------
    summary["SR"] = np.where(summary["Balls"] > 0, round((summary["Runs"] / summary["Balls"]) * 100, 1), 0.0)
    summary["SR10"] = np.where(summary["SR10_Balls"] > 0, round((summary["SR10_Runs"] / summary["SR10_Balls"]) * 100, 1), 0.0)
    summary["Avg"] = np.where(summary["Dismissals"] > 0, round(summary["Runs"] / summary["Dismissals"], 2), np.nan)

    summary["B/Dis"] = np.where(summary["Dismissals"] > 0, round(summary["Balls"] / summary["Dismissals"], 1), np.nan)
    summary["B/4"] = np.where(summary["Fours"] > 0, round(summary["Balls"] / summary["Fours"], 1), np.nan)
    summary["B/6"] = np.where(summary["Sixes"] > 0, round(summary["Balls"] / summary["Sixes"], 1), np.nan)
    summary["B/Bdy"] = np.where((summary["Fours"] + summary["Sixes"]) > 0, round(summary["Balls"] / (summary["Fours"] + summary["Sixes"]), 1), np.nan)

    summary["Bdy%"] = np.where(summary["Balls"] > 0, round((summary["Fours"] + summary["Sixes"]) / summary["Balls"] * 100, 1), 0.0)
    summary["BRns%"] = np.where(summary["Runs"] > 0, round(summary["BoundaryRuns"] / summary["Runs"] * 100, 1), 0.0)
    summary["NB-SR"] = np.where(summary["RunBalls"] > 0, round((summary["RunBallsRuns"] / summary["RunBalls"]) * 100, 1), 0.0)
    summary["Dot%"] = np.where(summary["Balls"] > 0, round(summary["DotBalls"] / summary["Balls"] * 100, 1), 0.0)
    summary["Run%"] = np.where(summary["Balls"] > 0, round(summary["RunBalls"] / summary["Balls"] * 100, 1), 0.0)

    summary["PP SR"] = np.where(summary["PP_Balls"] > 0, round((summary["PP_Runs"] / summary["PP_Balls"]) * 100, 1), 0.0)
    summary["Mid SR"] = np.where(summary["Mid_Balls"] > 0, round((summary["Mid_Runs"] / summary["Mid_Balls"]) * 100, 1), 0.0)
    summary["Dth SR"] = np.where(summary["Dth_Balls"] > 0, round((summary["Dth_Runs"] / summary["Dth_Balls"]) * 100, 1), 0.0)

    summary["SR-I"] = np.where(summary["SR_I_Balls"] > 0, round((summary["SR_I_Runs"] / summary["SR_I_Balls"]) * 100, 1), 0.0)
    summary["SR-II"] = np.where(summary["SR_II_Balls"] > 0, round((summary["SR_II_Runs"] / summary["SR_II_Balls"]) * 100, 1), 0.0)

    summary["Accel"] = np.where(summary["PP SR"] > 0, round(summary["Dth SR"] / summary["PP SR"], 2), np.nan)
    summary["30+%"] = np.where(summary["InningsCount"] > 0, round(summary["Innings30Plus"] / summary["InningsCount"] * 100, 1), 0.0)

    # Min balls filter:
    # If innings is selected, it applies on that filtered-innings subset.
    # If innings is not selected, it applies on the full filtered subset.
    if min_balls is not None:
        summary = summary[summary["Balls"] >= int(min_balls)]

    # Final output
    summary = summary.rename(columns={"bat": "Player"})
    summary = summary[
        [
            "Player", "Balls", "Runs", "HS", "SR", "SR10", "Avg",
            "B/Dis", "B/4", "B/6", "B/Bdy",
            "Bdy%", "BRns%", "NB-SR", "Dot%", "Run%",
            "PP SR", "Mid SR", "Dth SR", "Accel", "30+%",
            "SR-I", "SR-II",
        ]
    ].sort_values(by="Runs", ascending=False).reset_index(drop=True)

    return summary