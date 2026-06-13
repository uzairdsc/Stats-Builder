import streamlit as st
import pandas as pd
import boto3
from botocore.exceptions import NoCredentialsError

from StatsSum import batting_summary, bowler_summary

# ===== AUTH =====
APP_PASSWORD = st.secrets["auth"]["password"]

if "authenticated" not in st.session_state:
    st.session_state.authenticated = False

if not st.session_state.authenticated:
    st.title("❄️ Stats Builder APP Login")
    password_input = st.text_input("Enter Access Password:", type="password")
    if password_input == APP_PASSWORD:
        st.success("Access granted.")
        st.session_state.authenticated = True
        st.rerun()
    elif password_input:
        st.error("Invalid password. Try again.")
    st.stop()

st.set_page_config(page_title="Stats Builder App", page_icon="🏏", layout="wide")
st.title("🏏 Stats Builder - T20 Stats Dashboard")


@st.cache_data(ttl=60)  # Cache for 1 min
def load_from_s3(bucket_name, file_key, aws_access_key, aws_secret_key, region_name='us-east-1'):
    """Load CSV from S3 bucket"""
    try:
        s3_client = boto3.client(
            's3',
            aws_access_key_id=aws_access_key,
            aws_secret_access_key=aws_secret_key,
            region_name=region_name
        )
        with st.spinner(f"Loading data from S3: {file_key}..."):
            obj = s3_client.get_object(Bucket=bucket_name, Key=file_key)
            df = pd.read_csv(obj['Body'], low_memory=False)
            st.success(f"Loaded {len(df)} rows from S3")
            return df
    except NoCredentialsError:
        st.error("AWS credentials not found. Check your secrets.toml file.")
        return None
    except Exception as e:
        st.error(f"Error loading from S3: {str(e)}")
        return None


# ===== Dataset Selection =====
st.sidebar.header("📂 Select Dataset Source")
data_source = st.sidebar.selectbox(
    "Choose data source:",
    ["Upload Data File", "S3_since24", "S3_PSL-26", "S3_all", "Cache_all", "Cache_since24"]
)

if 'df' not in st.session_state:
    st.session_state.df = None
if 'batting_df' not in st.session_state:
    st.session_state.batting_df = None
if 'bowling_df' not in st.session_state:
    st.session_state.bowling_df = None

df = st.session_state.df

S3_DEFAULTS = {
    "S3_since24": ("t20_bbb_since_2024.csv", "load_2024"),
    "S3_PSL-26": ("t20_bbb_psl_2026.csv", "load_psl26"),
    "S3_all": ("t20_bbb_wt20.csv", "load_complete"),
}
CACHE_DEFAULTS = {
    "Cache_all": "E:/Cricket Related Projects/HG-Datasets/t20_bbb.csv",
    "Cache_since24": "E:/Cricket Related Projects/HG-Datasets/t20_bbb_since_2024.csv",
}

if data_source == "Upload Data File":
    uploaded_file = st.sidebar.file_uploader("Upload CSV File", type=["csv"])
    if uploaded_file:
        df = pd.read_csv(uploaded_file, low_memory=False)
        st.session_state.df = df
        st.sidebar.success(f"Loaded {len(df):,} rows")

elif data_source in S3_DEFAULTS:
    if "aws" in st.secrets:
        bucket = st.secrets["aws"]["bucket_name"]
        access_key = st.secrets["aws"]["access_key_id"]
        secret_key = st.secrets["aws"]["secret_access_key"]
        region = st.secrets["aws"].get("region_name", "ap-south-1")

        default_key, btn_key = S3_DEFAULTS[data_source]
        s3_file_key = st.sidebar.text_input("Enter S3 file path:", value=default_key)

        if st.sidebar.button("Load from S3", key=btn_key):
            loaded_df = load_from_s3(bucket, s3_file_key, access_key, secret_key, region)
            if loaded_df is not None:
                st.session_state.df = loaded_df
                df = loaded_df

        if st.session_state.df is not None:
            st.sidebar.info(f"Current data: {len(st.session_state.df):,} rows")
    else:
        st.sidebar.warning("⚠️ AWS credentials not configured in secrets.toml")

elif data_source in CACHE_DEFAULTS:
    local_file_path = st.sidebar.text_input(
        "Enter local file path:",
        value=CACHE_DEFAULTS[data_source]
    )

    if st.sidebar.button("Load from Local Storage", key=f"load_{data_source}"):
        try:
            with st.spinner(f"Loading data from {local_file_path}..."):
                loaded_df = pd.read_csv(local_file_path, low_memory=False)
                st.session_state.df = loaded_df
                df = loaded_df
                st.sidebar.success(f"Loaded {len(loaded_df):,} rows from local storage")
        except FileNotFoundError:
            st.sidebar.error(f"File not found: {local_file_path}")
        except Exception as e:
            st.sidebar.error(f"Error loading file: {str(e)}")

    if st.session_state.df is not None:
        st.sidebar.info(f"Current data: {len(st.session_state.df):,} rows")

# Refresh / clear data buttons
if st.session_state.df is not None:
    col_refresh, col_clear = st.sidebar.columns(2)
    with col_refresh:
        if st.button("🔄 Refresh Data", key="refresh_data_btn"):
            st.cache_data.clear()
            st.rerun()
    with col_clear:
        if st.button("🗑️ Clear Data", key="clear_data_btn"):
            st.cache_data.clear()
            st.session_state.df = None
            st.session_state.batting_df = None
            st.session_state.bowling_df = None
            st.rerun()

# Widget keys used by filters (for Clear Filters)
FILTER_KEYS = [
    "f_date_range", "f_competition", "f_match", "f_mcode",
    "f_team_bat", "f_batter", "f_bat_hand", "f_ground",
    "f_team_bowl", "f_bowler", "f_bowl_type", "f_bowl_kind",
    "f_bowl_arm", "f_inns", "f_overs", "f_phase", "f_min_balls",
]

# ===== Header tooltips (clear metric definitions) =====
BAT_COL_CONFIG = {
    "Player": st.column_config.TextColumn("Player", help="Player name"),
    "Balls": st.column_config.NumberColumn("Balls", help="Legal balls faced"),
    "Runs": st.column_config.NumberColumn("Runs", help="Total runs scored"),
    "HS": st.column_config.NumberColumn("HS", help="Highest score in an innings"),
    "SR": st.column_config.NumberColumn("SR", help="Strike rate (runs per 100 balls)"),
    "SR10": st.column_config.NumberColumn("SR10", help="Strike rate over the first 10 balls of each innings"),
    "Avg": st.column_config.NumberColumn("Avg", help="Batting average (runs per dismissal)"),
    "B/Dis": st.column_config.NumberColumn("B/Dis", help="Balls faced per dismissal"),
    "B/4": st.column_config.NumberColumn("B/4", help="Balls faced per four hit"),
    "B/6": st.column_config.NumberColumn("B/6", help="Balls faced per six hit"),
    "B/Bdy": st.column_config.NumberColumn("B/Bdy", help="Balls faced per boundary (fours and sixes combined)"),
    "Bdy%": st.column_config.NumberColumn("Bdy%", help="% of balls faced that were hit for a boundary"),
    "BRns%": st.column_config.NumberColumn("BRns%", help="% of total runs scored from boundaries"),
    "NB-SR": st.column_config.NumberColumn("NB-SR", help="Strike rate on non-boundary scoring balls (1s, 2s, 3s)"),
    "Dot%": st.column_config.NumberColumn("Dot%", help="% of balls faced that were dot balls"),
    "Run%": st.column_config.NumberColumn("Run%", help="% of balls faced that scored 1-3 runs"),
    "PP SR": st.column_config.NumberColumn("PP SR", help="Powerplay strike rate (overs 1-6)"),
    "Mid SR": st.column_config.NumberColumn("Mid SR", help="Middle overs strike rate (overs 7-15)"),
    "Dth SR": st.column_config.NumberColumn("Dth SR", help="Death overs strike rate (overs 16-20)"),
    "Accel": st.column_config.NumberColumn("Accel", help="Acceleration: death-overs SR divided by powerplay SR"),
    "30+%": st.column_config.NumberColumn("30+%", help="% of innings where the batter scored 30 or more"),
    "SR-I": st.column_config.NumberColumn("SR-I", help="Strike rate in the first innings"),
    "SR-II": st.column_config.NumberColumn("SR-II", help="Strike rate in the second innings"),
}
BOWL_COL_CONFIG = {
    "Player": st.column_config.TextColumn("Player", help="Player name"),
    "Balls": st.column_config.NumberColumn("Balls", help="Legal balls bowled"),
    "Wkts": st.column_config.NumberColumn("Wkts", help="Total wickets taken"),
    "Econ": st.column_config.NumberColumn("Econ", help="Runs conceded per 6 legal balls"),
    "Avg": st.column_config.NumberColumn("Avg", help="Runs conceded per wicket"),
    "SR": st.column_config.NumberColumn("SR", help="Balls bowled per wicket"),
    "B/4": st.column_config.NumberColumn("B/4", help="Balls bowled per four conceded"),
    "B/6": st.column_config.NumberColumn("B/6", help="Balls bowled per six conceded"),
    "B/Bdy": st.column_config.NumberColumn("B/Bdy", help="Balls bowled per boundary conceded (fours and sixes combined)"),
    "Bdy%": st.column_config.NumberColumn("Bdy%", help="% of balls bowled that were hit for a boundary"),
    "NB-Econ": st.column_config.NumberColumn("NB-Econ", help="Economy rate on non-boundary balls"),
    "Wkt%": st.column_config.NumberColumn("Wkt%", help="% of legal balls that took a wicket"),
    "Dot%": st.column_config.NumberColumn("Dot%", help="% of legal balls that were dot balls"),
    "PP Econ": st.column_config.NumberColumn("PP Econ", help="Powerplay economy rate (overs 1-6)"),
    "PP Wkts": st.column_config.NumberColumn("PP Wkts", help="Wickets taken in the powerplay"),
    "PP Dot%": st.column_config.NumberColumn("PP Dot%", help="Dot ball % in the powerplay"),
    "Mid Eco": st.column_config.NumberColumn("Mid Eco", help="Middle overs economy rate (overs 7-15)"),
    "Mid Wkts": st.column_config.NumberColumn("Mid Wkts", help="Wickets taken in the middle overs"),
    "Mid Dot%": st.column_config.NumberColumn("Mid Dot%", help="Dot ball % in the middle overs"),
    "Dth Econ": st.column_config.NumberColumn("Dth Econ", help="Death overs economy rate (overs 16-20)"),
    "Dth Wkts": st.column_config.NumberColumn("Dth Wkts", help="Wickets taken in the death overs"),
    "Dth Dot%": st.column_config.NumberColumn("Dth Dot%", help="Dot ball % in the death overs"),
    "Dth 6s": st.column_config.NumberColumn("Dth 6s", help="Sixes conceded in the death overs"),
    "SR-I": st.column_config.NumberColumn("SR-I", help="Balls bowled per wicket in the first innings"),
    "SR-II": st.column_config.NumberColumn("SR-II", help="Balls bowled per wicket in the second innings"),
    "Pressure": st.column_config.NumberColumn("Pressure", help="Composite 0-100 score: Dot% (40%) + economy vs benchmark (35%) + wicket rate (25%)"),
}


def opts(frame, col):
    """Unique sorted options for a column (linear - always from full df)."""
    if col in frame.columns:
        return sorted(frame[col].dropna().unique())
    return []


# ===== Main App Logic =====
if df is not None:
    if 'date' in df.columns and df['date'].dtype != 'datetime64[ns]':
        df['date'] = pd.to_datetime(df['date'], errors='coerce')

    st.markdown("---")
    st.subheader("Filter Options")

    # All filter options come from the full df (linear, no cascading)
    with st.form("filters_form"):
        c1, c2, c3, c4 = st.columns(4)

        # ----- Column 1: Date, Competition, Match, Match Code -----
        with c1:
            if 'date' in df.columns:
                valid_dates = df['date'].dropna()
                if not valid_dates.empty:
                    min_d, max_d = valid_dates.min().date(), valid_dates.max().date()
                    st.date_input("Date Range", value=(min_d, max_d),
                                  min_value=min_d, max_value=max_d, key="f_date_range")

            st.selectbox("Competition", ["All"] + opts(df, 'competition'), key="f_competition")
            st.multiselect("Match Number", [int(m) for m in opts(df, 'p_match')], key="f_match")
            st.multiselect("Match Code", opts(df, 'mcode'), key="f_mcode")

        # ----- Column 2: Batting side -----
        with c2:
            st.multiselect("Batting Team", opts(df, 'team_bat'), key="f_team_bat")
            st.multiselect("Batter", opts(df, 'bat'), key="f_batter")
            st.multiselect("Batter Hand(s)", opts(df, 'bat_hand'), key="f_bat_hand")
            st.multiselect("Venue", opts(df, 'ground'), key="f_ground")

        # ----- Column 3: Bowling side -----
        with c3:
            st.multiselect("Bowling Team", opts(df, 'team_bowl'), key="f_team_bowl")
            st.multiselect("Bowler", opts(df, 'bowl'), key="f_bowler")
            st.multiselect("Bowler Kind(s)", opts(df, 'bowl_type'), key="f_bowl_type")
            st.multiselect("Bowler Type(s)", opts(df, 'bowl_kind'), key="f_bowl_kind")

        # ----- Column 4: Arm, Innings, Overs, Phase -----
        with c4:
            st.multiselect("Bowler Arm(s)", opts(df, 'bowl_arm'), key="f_bowl_arm")
            st.multiselect("Innings", [int(i) for i in opts(df, 'inns')], key="f_inns")
            st.multiselect("Overs", [int(o) for o in opts(df, 'over')], key="f_overs")
            st.multiselect("Phase", ["Powerplay (1-6)", "Middle (7-15)", "Slog (16-20)"], key="f_phase")

        # ----- Minimum balls filter -----
        st.number_input("Minimum Balls", min_value=0, value=50, step=5, key="f_min_balls",
                        help="Only include players with at least this many balls (faced for batting, bowled for bowling)")

        # ----- Buttons: clear (col 2) and apply (col 3) -----
        b1, b2, b3, b4 = st.columns(4)
        with b2:
            clear_clicked = st.form_submit_button("🧹 Clear Filters", use_container_width=True)
        with b3:
            apply_clicked = st.form_submit_button("✅ Apply Filters", type="primary", use_container_width=True)

    # Clear: reset all filter widgets and results
    if clear_clicked:
        for k in FILTER_KEYS:
            st.session_state.pop(k, None)
        st.session_state.batting_df = None
        st.session_state.bowling_df = None
        st.rerun()

    # Apply: run BOTH summaries once with the same filter set
    if apply_clicked:
        s = st.session_state

        date_from, date_to = None, None
        dr = s.get("f_date_range")
        if isinstance(dr, (list, tuple)) and len(dr) == 2:
            date_from, date_to = dr[0], dr[1]

        phase_map = {"Powerplay (1-6)": 1, "Middle (7-15)": 2, "Slog (16-20)": 3}
        phase_sel = [phase_map[p] for p in s.get("f_phase", [])]

        comp = s.get("f_competition", "All")

        common_kwargs = dict(
            player_name=s.get("f_batter") or None,
            team_bat=s.get("f_team_bat") or None,
            team_bowl=s.get("f_team_bowl") or None,
            bowler_name=s.get("f_bowler") or None,
            competition=None if comp == "All" else comp,
            mat_num=s.get("f_match") or None,
            mcode=s.get("f_mcode") or None,
            inns=s.get("f_inns") or None,
            over_values=s.get("f_overs") or None,
            phase=phase_sel or None,
            date_from=date_from,
            date_to=date_to,
            ground=s.get("f_ground") or None,
            bat_hand=s.get("f_bat_hand") or None,
            bowl_type=s.get("f_bowl_type") or None,
            bowl_kind=s.get("f_bowl_kind") or None,
            bowl_arm=s.get("f_bowl_arm") or None,
            min_balls=s.get("f_min_balls") or None,
        )

        with st.spinner("Computing batting & bowling summaries..."):
            st.session_state.batting_df = batting_summary(df, **common_kwargs)
            st.session_state.bowling_df = bowler_summary(df, **common_kwargs)

    # ===== Results Section =====
    batting_df = st.session_state.batting_df
    bowling_df = st.session_state.bowling_df

    if batting_df is not None or bowling_df is not None:
        st.markdown("---")

        # Top control row: view toggle (left) + rows dropdown (right)
        view_col, _, rows_col = st.columns([2, 4, 1])
        with view_col:
            view = st.segmented_control(
                "View", ["Batting", "Bowling"], default="Batting",
                key="stats_view", label_visibility="collapsed"
            ) or "Batting"
        with rows_col:
            rows_to_show = st.selectbox("Rows", [10, 20, 50, 100, 200, 500], key="rows_to_show")

        if view == "Batting":
            result_df, col_config, label = batting_df, BAT_COL_CONFIG, "Batting Summary"
        else:
            result_df, col_config, label = bowling_df, BOWL_COL_CONFIG, "Bowling Summary"

        if result_df is None or result_df.empty:
            st.error("⚠️ No data available for the selected filters. Please adjust your filter selections.")
        else:
            st.markdown(f"**📊 {label}** — {len(result_df):,} players found")
            display_df = result_df.head(rows_to_show).copy()
            display_df.index = range(1, len(display_df) + 1)
            st.dataframe(
                display_df,
                use_container_width=True,
                height=420,
                column_config=col_config,
            )
else:
    st.info("Please select a dataset source to begin.")