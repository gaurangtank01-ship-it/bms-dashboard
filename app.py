import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt
import matplotlib.dates as mdates
import matplotlib.ticker as ticker
import re

plt.rcParams['axes.axisbelow'] = True

st.set_page_config(layout="wide")
st.title("🔋 Battery Analysis Dashboard (Pro) 🚚")

# =========================
# 🚗 CHASSIS INPUT
# =========================
chassis_number = st.text_input("🚗 Enter Chassis Number")

# =========================
# 🧠 ERROR MAP
# =========================
error_map = {
    0: "ERROR_GENERAL_IOB", 1: "ERROR_GENERAL_NULLPOINT", 2: "ERROR_GENERAL_PAOB",
    3: "ERROR_CAN_RX_TIMEOUT", 4: "ERROR_INVALID_TIME_FROM_RTC",
    5: "ERROR_CELL_VDELTA", 6: "ERROR_CELL_TDELTA",
    7: "ERROR_TEMP_AUX_NO_VALUE", 8: "ERROR_TEMP_AUX_SHORTED",
    9: "ERROR_TEMP_AUX_OPEN",
    10: "ERROR_TEMP_AUX_MIN_CH01", 11: "ERROR_TEMP_AUX_MIN_CH02",
    12: "ERROR_TEMP_AUX_MIN_CH03", 13: "ERROR_TEMP_AUX_MIN_CH04",
    14: "ERROR_TEMP_AUX_MIN_CH05", 15: "ERROR_TEMP_AUX_MIN_CH06",
    16: "ERROR_TEMP_AUX_MIN_CH07", 17: "ERROR_TEMP_AUX_MIN_CH08",
    18: "ERROR_TEMP_AUX_MAX_CH01", 19: "ERROR_TEMP_AUX_MAX_CH02",
    20: "ERROR_TEMP_AUX_MAX_CH03", 21: "ERROR_TEMP_AUX_MAX_CH04",
    22: "ERROR_TEMP_AUX_MAX_CH05", 23: "ERROR_TEMP_AUX_MAX_CH06",
    24: "ERROR_TEMP_AUX_MAX_CH07", 25: "ERROR_TEMP_AUX_MAX_CH08",
    26: "ERROR_SYS_LIM_CELL_V_MIN", 27: "ERROR_SYS_LIM_CELL_V_MAX",
    28: "ERROR_SYS_LIM_CELL_T_MIN", 29: "ERROR_SYS_LIM_CELL_T_MAX",
    30: "ERROR_SYS_LIM_PACK_I_IN", 31: "ERROR_SYS_LIM_PACK_I_OUT",
    32: "ERROR_SYS_LIM_PACK_I2T",
    33: "ERROR_SYS_CELL_V_NO_VALUE", 34: "ERROR_SYS_CELL_T_NO_VALUE",
    35: "ERROR_SYS_CELL_T_SHORTED", 36: "ERROR_SYS_CELL_T_OPEN",
    37: "ERROR_SYS_CMU_PCB_T_NO_VALUE", 38: "ERROR_SYS_CMU_PCB_T_SHORTED",
    39: "ERROR_SYS_CMU_PCB_T_OPEN",
    40: "ERROR_SYS_FB_LOAD_NEG_MISSING", 41: "ERROR_SYS_FB_LOAD_POS_MISSING",
    42: "ERROR_SYS_FB_PRE_CHARGE_MISSING", 43: "ERROR_SYS_FB_CHG_NEG_MISSING",
    44: "ERROR_SYS_FB_LOAD_NEG_WELDED", 45: "ERROR_SYS_FB_LOAD_POS_WELDED",
    46: "ERROR_SYS_FB_PRE_CHARGE_WELDED", 47: "ERROR_SYS_FB_CHG_NEG_WELDED",
    48: "ERROR_SYS_CONTACTOR_RETRIES",
    49: "ERROR_SYS_LIM_CHG_I_OVER_UNDER",
    50: "ERROR_SYS_OPEN_WIRE", 51: "ERROR_SYS_ESTOP",
    52: "CONTACTOR_PRE_CHARGE_OPENC", 53: "CONTACTOR_PRE_CHARGE_SHORT",
    54: "CONTACTOR_POS_OPENC", 55: "CONTACTOR_SHORT",
    56: "CONTACTOR_PRE_CHARGE_TIMEOUT",
    57: "RESISTANCE_TOO_HIGH", 58: "DUPLICATE_NODE",
    59: "MISCHARGE", 60: "MISLOAD",
    61: "CHARGE_NO_RESPONSE",
    62: "ERROR_READY_CURRENT_HIGH", 63: "ERROR_AFE"
}

# =========================
# 🔍 DECODER
# =========================
def decode_error(val):
    if pd.isna(val):
        return "No Error"

    try:
        nums = list(map(int, re.findall(r'\d+', str(val))))
        if not nums:
            return "No Error"
        return ", ".join([f"{n} = {error_map.get(n, 'UNKNOWN')}" for n in sorted(set(nums))])
    except:
        return "No Error"

# =========================
# 📂 FILE UPLOAD
# =========================
file = st.file_uploader("📂 Upload Excel file", type=["xlsx"])

if file:
    df = pd.read_excel(file, dtype={'bmsActiveErrorBits': str})
    df.columns = df.columns.str.strip()
    # =========================
    # 🧹 CLEAN BMS ERROR COLUMN
    df['bmsActiveErrorBits'] = df['bmsActiveErrorBits'].replace(
        [None, "", " ", "nan", "NaN"], pd.NA
    )    

    df['bmsActiveErrorBits'] = df['bmsActiveErrorBits'].astype(str).str.strip()
    df.loc[df['bmsActiveErrorBits'] == "", 'bmsActiveErrorBits'] = pd.NA

    # OPTIONAL: treat 0 as no error (ONLY if needed)
    # df.loc[df['bmsActiveErrorBits'] == '0', 'bmsActiveErrorBits'] = pd.NA

    required_cols = [
        'createdAt',
        'batteryStateOfCharge',
        'batteryMaxVoltage',
        'batteryMinVoltage',
        'bmsActiveErrorBits',
        'odometer',
        'batteryBmsConfigId'
    ]

    missing_cols = [c for c in required_cols if c not in df.columns]

    if missing_cols:
        st.error("❌ Missing required columns:")

        for col in missing_cols:
            st.write(f"❌ {col}")

        st.divider()

        st.subheader("📋 Columns in your file:")
        st.write(list(df.columns))

        st.divider()

        st.subheader("🔍 Possible matches (check naming):")
        for req in missing_cols:
            matches = [c for c in df.columns if req.lower() in c.lower()]
            if matches:
                st.write(f"👉 {req} → {matches}")
            else:
                st.write(f"👉 {req} → ❌ No close match found")

        st.stop()

    else:
        df = df[required_cols].copy()

        df['createdAt'] = pd.to_datetime(df['createdAt'], errors='coerce')
        df = df.dropna(subset=['createdAt'])
        df = df.sort_values('createdAt')

        df['createdAt_num'] = mdates.date2num(df['createdAt'])

        df['cellImbalance'] = df['batteryMaxVoltage'] - df['batteryMinVoltage']

        max_idx = df['cellImbalance'].idxmax()
        min_v = df['batteryMinVoltage'].min()
        max_v = df['batteryMaxVoltage'].max()

        # =========================
        # HEADER
        # =========================
        st.subheader("📊 Vehicle Info")
        st.write(f"🚗 Chassis Number: {chassis_number if chassis_number else 'Not Entered'}")

        c1, c2, c3, c4 = st.columns(4)
        c1.metric("⚖️ Max Imbalance", f"{df['cellImbalance'].max():.3f}")
        c2.metric("🔋 Max Voltage", f"{df['batteryMaxVoltage'].max():.2f}")
        c3.metric("🪫 Min Voltage", f"{df['batteryMinVoltage'].min():.2f}")
        c4.metric("⚡ SOC @ Max Imbalance", f"{df.loc[max_idx,'batteryStateOfCharge']:.2f}")

        st.write(f"📍 Time: {df.loc[max_idx,'createdAt']}")
        st.write(f"🚗 Odometer: {df.loc[max_idx,'odometer']}")
        # ===== SMART ERROR DETECTION =====
        window = 5  # you can change to 3–10

        start = max(0, max_idx - window)
        end = min(len(df), max_idx + window + 1)

        subset = df.iloc[start:end]

        # filter real errors (ignore 0 / empty)
        errors_nearby = subset[
            subset[error_col].astype(str).str.contains(r'\d') &
            (subset[error_col].astype(str) != '0')
        ]

        if not errors_nearby.empty:
            combined = ",".join(errors_nearby[error_col].astype(str).unique())
            st.write(f"⚠️ BMS Error (near peak): {decode_error(combined)}")
        else:
            st.write("⚠️ BMS Error: No Error near peak imbalance")
            
            st.write(f"🔧 BMS Config ID: {df.loc[max_idx,'batteryBmsConfigId']}")

        st.divider()

        # =========================
        # GRAPH 1
        # =========================
        fig, ax1 = plt.subplots(figsize=(12,5))

        ax1.plot(df['createdAt'], df['batteryMaxVoltage'], color='purple', linewidth=2)
        ax1.plot(df['createdAt'], df['batteryMinVoltage'], color='orange', linewidth=2)


        ax1.set_ylim(min_v - 100, max_v + 100)

        ax2 = ax1.twinx()
        ax2.plot(df['createdAt'], df['batteryStateOfCharge'], color='green', linewidth=2)
        ax2.plot(df['createdAt'], df['cellImbalance'], color='red', linewidth=2)

        locator = mdates.AutoDateLocator()
        formatter = mdates.DateFormatter('%H:%M')

        ax1.xaxis.set_major_locator(locator)
        ax1.xaxis.set_major_formatter(formatter)

        ax1.tick_params(axis='x', rotation=90, labelsize=8)

        ax1.grid(True, linestyle='--', linewidth=0.6)

        fig.legend(["Max Voltage", "Min Voltage", "SOC", "Imbalance"],
                   loc="upper center", ncol=4, bbox_to_anchor=(0.5, 1.15))

        fig.tight_layout()
        st.pyplot(fig)

        st.divider()

        # =========================
        # GRAPH 2
        # =========================
        fig2, ax3 = plt.subplots(figsize=(12,4))

        ax3.plot(df['createdAt'], df['cellImbalance'], color='red', linewidth=2)

        ax4 = ax3.twinx()
        ax4.plot(df['createdAt'], df['batteryStateOfCharge'], color='green', linewidth=2)

        ax4.set_ylim(0, 100)
        ax4.yaxis.set_major_locator(ticker.MultipleLocator(10))
        ax4.yaxis.set_minor_locator(ticker.MultipleLocator(5))

        ax3.xaxis.set_major_locator(locator)
        ax3.xaxis.set_major_formatter(formatter)

        ax3.tick_params(axis='x', rotation=90, labelsize=8)

        ax3.grid(True, linestyle='--', linewidth=0.6)

        fig2.legend(["Imbalance", "SOC"],
                    loc="upper center", ncol=2, bbox_to_anchor=(0.5, 1.2))

        fig2.tight_layout()
        st.pyplot(fig2)

        st.divider()

        # =========================
        # ERROR TABLE
        # =========================
        st.subheader("⚠️ Error Log")

        err_df = df[df['bmsActiveErrorBits'].astype(str).str.contains(r'\d')].copy()
        err_df['Decoded'] = err_df['bmsActiveErrorBits'].apply(decode_error)

        if not err_df.empty:
            st.dataframe(err_df[['createdAt', 'bmsActiveErrorBits', 'Decoded']])
        else:
            st.success("✅ No Errors Found")