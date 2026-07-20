import base64
import html
import io

import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt
from datetime import date, datetime
from pathlib import Path

import helpers
import ai_helper
from helpers import (
    INCOME_FILE,
    EXPENSES_FILE,
    GOALS_FILE,
    INCOME_COLUMNS,
    EXPENSES_COLUMNS,
    GOALS_COLUMNS,
    EXPENSE_CATEGORIES,
    ALL_TIME,
)

# ============================================================
# WiseBudget AI
# An AI-Powered Budgeting and Investment Education Assistant
# ============================================================

# Brand assets (cropped from the original reference image by
# scripts/create_logo_assets.py). The app falls back to plain text/emoji if
# the files are missing, so a fresh clone still runs.
ASSETS_FOLDER = Path("assets")
LOGO_FILE = ASSETS_FOLDER / "wisebudget-logo.png"
ICON_FILE = ASSETS_FOLDER / "wisebudget-icon.png"

st.set_page_config(
    page_title="WiseBudget AI",
    page_icon=str(ICON_FILE) if ICON_FILE.exists() else "💷",
    layout="wide"
)


def inject_custom_css():
    """
    Global styling for WiseBudget AI.

    The previous desktop styling looked good, but some Streamlit Cloud/mobile
    elements rendered with very low contrast. This CSS keeps the premium look
    while forcing readable text, mobile-safe cards and compact charts.
    """
    st.markdown("""
    <style>
    /* ============================================================
       Base app styling
       ============================================================ */

    :root {
        --wb-navy: #071A2D;
        --wb-emerald: #10B981;
        --wb-emerald-dark: #0DA271;
        --wb-mint: #ECFDF5;
        --wb-bg: #F3F6FA;
        --wb-card: #FFFFFF;
        --wb-muted: #64748B;
        --wb-border: #E2E8F0;
        --wb-amber: #F59E0B;
        --wb-red: #EF4444;
    }

    .stApp {
        background:
            radial-gradient(circle at top left, rgba(16, 185, 129, 0.10), transparent 32rem),
            linear-gradient(180deg, #F3F6FA 0%, #EEF4F8 55%, #ECFDF5 100%);
        background-attachment: fixed;
        color: var(--wb-navy) !important;
    }

    .block-container {
        padding-top: 2.2rem !important;
        padding-bottom: 3rem !important;
        max-width: 1180px;
    }

    /* Tidy Streamlit chrome WITHOUT hiding the header. The header holds the
       sidebar open/close arrow - hiding it strands mobile users with no way
       to reopen a closed sidebar. Only decorative extras are hidden. */
    footer,
    [data-testid="stDecoration"],
    [data-testid="stStatusWidget"],
    .stDeployButton {
        display: none !important;
    }

    /* Keep the header visible but blend it into the app background so the
       sidebar arrow and menu stay usable without a big white bar. */
    [data-testid="stHeader"] {
        background: rgba(243, 246, 250, 0.72) !important;
        backdrop-filter: blur(6px);
    }

    /* Safety net: the sidebar open/close controls must never be hidden or
       faded by the readability overrides above. */
    [data-testid="stSidebarCollapsedControl"],
    [data-testid="stSidebarCollapsedControl"] *,
    [data-testid="stExpandSidebarButton"],
    [data-testid="stSidebarCollapseButton"],
    [data-testid="collapsedControl"] {
        visibility: visible !important;
        opacity: 1 !important;
    }

    /* Hide heading anchor/link icons. */
    [data-testid="stHeaderActionElements"],
    .stMarkdown h1 a,
    .stMarkdown h2 a,
    .stMarkdown h3 a,
    .stMarkdown h4 a {
        display: none !important;
        visibility: hidden !important;
    }

    /* ============================================================
       Readability fixes - especially for phone and Streamlit Cloud
       ============================================================ */

    html,
    body,
    .stApp,
    .stApp div,
    .stApp p,
    .stApp span,
    .stApp label,
    .stApp li,
    .stApp td,
    .stApp th {
        color: var(--wb-navy) !important;
        opacity: 1 !important;
    }

    h1, h2, h3, h4, h5, h6 {
        color: var(--wb-navy) !important;
        opacity: 1 !important;
        letter-spacing: -0.02em;
    }

    p, li, label, span {
        line-height: 1.55;
    }

    small,
    .caption,
    [data-testid="stCaptionContainer"],
    [data-testid="stCaptionContainer"] *,
    .small-muted,
    .muted,
    [class*="muted"] {
        color: var(--wb-muted) !important;
        opacity: 1 !important;
    }

    /* Streamlit metrics sometimes inherit a very faint colour on mobile.
       These rules make the numbers readable and prevent ellipsis where possible. */
    [data-testid="stMetric"],
    [data-testid="stMetric"] *,
    [data-testid="stMetricLabel"],
    [data-testid="stMetricValue"],
    [data-testid="stMetricDelta"] {
        color: var(--wb-navy) !important;
        opacity: 1 !important;
    }

    [data-testid="stMetricValue"] {
        font-weight: 800 !important;
        font-size: 1.85rem !important;
        white-space: normal !important;
        overflow: visible !important;
        text-overflow: clip !important;
        line-height: 1.15 !important;
    }

    [data-testid="stMetricLabel"] {
        color: var(--wb-muted) !important;
        font-weight: 600 !important;
    }

    /* Expander/card content must never fade to white. */
    [data-testid="stExpander"],
    [data-testid="stExpander"] *,
    .streamlit-expanderContent,
    .streamlit-expanderContent * {
        color: var(--wb-navy) !important;
        opacity: 1 !important;
    }

    /* Inputs/selects/radios. */
    input,
    textarea,
    select,
    [data-baseweb="select"] *,
    [role="radiogroup"] *,
    [data-testid="stSelectbox"] *,
    [data-testid="stTextInput"] *,
    [data-testid="stTextArea"] *,
    [data-testid="stNumberInput"] * {
        color: var(--wb-navy) !important;
        opacity: 1 !important;
    }

    /* ============================================================
       Sidebar
       ============================================================ */

    [data-testid="stSidebar"] {
        background: linear-gradient(180deg, #FFFFFF 0%, #F7FBF9 100%) !important;
        border-right: 1px solid var(--wb-border);
    }

    [data-testid="stSidebar"] * {
        color: var(--wb-navy) !important;
        opacity: 1 !important;
    }

    .wb-side-name {
        font-weight: 800;
        color: var(--wb-navy) !important;
        font-size: 1.05rem;
    }

    .wb-ai-pill {
        border-radius: 999px;
        padding: 0.32rem 0.8rem;
        font-size: 0.8rem;
        font-weight: 700;
        display: inline-block;
        margin-top: 0.2rem;
    }

    .wb-ai-on {
        background: #D1FAE5;
        color: #065F46 !important;
        border: 1px solid var(--wb-emerald);
    }

    .wb-ai-off {
        background: #FEF3C7;
        color: #92400E !important;
        border: 1px solid var(--wb-amber);
    }

    /* ============================================================
       Buttons
       ============================================================ */

    .stButton > button,
    .stFormSubmitButton > button {
        background-color: var(--wb-emerald) !important;
        color: #FFFFFF !important;
        border: none !important;
        border-radius: 12px !important;
        padding: 0.5rem 1.1rem !important;
        font-weight: 700 !important;
        min-height: 2.5rem !important;
        transition: all 0.15s ease !important;
    }

    .stButton > button *,
    .stFormSubmitButton > button * {
        color: #FFFFFF !important;
    }

    .stButton > button:hover,
    .stFormSubmitButton > button:hover {
        background-color: var(--wb-emerald-dark) !important;
        color: #FFFFFF !important;
        box-shadow: 0 5px 14px rgba(16, 185, 129, 0.30) !important;
        transform: translateY(-1px);
    }

    .stDownloadButton > button {
        background-color: #FFFFFF !important;
        color: var(--wb-navy) !important;
        border: 1px solid #CBD5E1 !important;
        border-radius: 12px !important;
        font-weight: 700 !important;
    }

    .stDownloadButton > button:hover {
        border-color: var(--wb-emerald) !important;
        color: var(--wb-emerald-dark) !important;
    }

    /* ============================================================
       Cards and containers
       ============================================================ */

    [data-testid="stMetric"] {
        background: linear-gradient(180deg, #FFFFFF 0%, #FBFDFF 100%) !important;
        border: 1px solid var(--wb-border) !important;
        border-radius: 16px !important;
        padding: 0.95rem 1.05rem !important;
        box-shadow: 0 4px 14px rgba(7, 26, 45, 0.07) !important;
    }

    [data-testid="stExpander"] {
        background-color: #FFFFFF !important;
        border: 1px solid var(--wb-border) !important;
        border-radius: 16px !important;
        box-shadow: 0 4px 14px rgba(7, 26, 45, 0.05) !important;
        overflow: hidden;
    }

    [data-testid="stExpander"] summary {
        font-weight: 700 !important;
        color: var(--wb-navy) !important;
        background: #F8FAFC !important;
        padding: 0.8rem 1rem !important;
    }

    [data-testid="stVerticalBlockBorderWrapper"] {
        background-color: rgba(255, 255, 255, 0.78) !important;
        border: 1px solid var(--wb-border) !important;
        border-radius: 16px !important;
        box-shadow: 0 4px 14px rgba(7, 26, 45, 0.05) !important;
    }

    [data-testid="stForm"] {
        background-color: #FFFFFF !important;
        border: 1px solid var(--wb-border) !important;
        border-radius: 16px !important;
        box-shadow: 0 4px 14px rgba(7, 26, 45, 0.05) !important;
        padding: 1rem 1.1rem !important;
    }

    [data-testid="stChatMessage"] {
        background-color: #FFFFFF !important;
        border: 1px solid var(--wb-border) !important;
        border-radius: 16px !important;
    }

    div[data-testid="stAlert"] {
        border-radius: 12px !important;
    }

    .stTextInput input,
    .stNumberInput input,
    .stTextArea textarea {
        border-radius: 10px !important;
        background: #FFFFFF !important;
    }

    /* Metric boxes nested inside expanded opportunity cards go flat so the
       card stays readable and compact. */
    [data-testid="stExpander"] [data-testid="stMetric"] {
        border: none !important;
        box-shadow: none !important;
        background: transparent !important;
        padding: 0.15rem 0 !important;
    }

    /* ============================================================
       Custom WiseBudget components
       ============================================================ */

    .wb-header-title {
        font-size: 1.9rem;
        font-weight: 850;
        color: var(--wb-navy) !important;
        margin: 0;
        line-height: 1.15;
    }

    .wb-header-sub {
        color: var(--wb-muted) !important;
        margin: 0.15rem 0 0.45rem 0;
        font-size: 0.98rem;
    }

    .wb-badge {
        display: inline-block;
        background: #FFFFFF;
        color: var(--wb-navy) !important;
        border: 1px solid var(--wb-border);
        border-radius: 999px;
        padding: 0.18rem 0.65rem;
        font-size: 0.76rem;
        font-weight: 700;
        margin-right: 0.35rem;
        margin-bottom: 0.3rem;
        box-shadow: 0 1px 3px rgba(7, 26, 45, 0.06);
    }

    .wb-disclaimer {
        background: var(--wb-mint);
        border: 1px solid #C7F0DF;
        color: #334155 !important;
        border-radius: 12px;
        padding: 0.62rem 0.85rem;
        font-size: 0.88rem;
        margin: 0.7rem 0 0.3rem 0;
    }

    .wb-demo-banner {
        background: linear-gradient(90deg, #FEF3C7 0%, #FDEBC8 100%);
        border: 1px solid #FBD38D;
        border-left: 5px solid var(--wb-amber);
        color: #92400E !important;
        border-radius: 12px;
        padding: 0.5rem 0.85rem;
        font-weight: 700;
        font-size: 0.88rem;
        margin-bottom: 0.7rem;
        box-shadow: 0 2px 8px rgba(245, 158, 11, 0.10);
    }

    .wb-action-card {
        background: #FFFFFF;
        border: 1px solid var(--wb-border);
        border-left: 5px solid var(--wb-emerald);
        border-radius: 16px;
        padding: 0.85rem 1rem;
        margin-bottom: 0.65rem;
        box-shadow: 0 4px 14px rgba(7, 26, 45, 0.06);
    }

    .wb-action-title {
        font-weight: 800;
        color: var(--wb-navy) !important;
    }

    .wb-action-saving {
        color: var(--wb-emerald) !important;
        font-weight: 800;
        font-size: 0.96rem;
        margin: 0.18rem 0;
    }

    .wb-action-step {
        color: #334155 !important;
        font-size: 0.9rem;
    }

    .wb-priority {
        float: right;
        border-radius: 999px;
        padding: 0.12rem 0.6rem;
        font-size: 0.72rem;
        font-weight: 800;
    }

    .wb-priority-high {
        background: #FEF3C7;
        color: #92400E !important;
    }

    .wb-priority-medium {
        background: #E0EAFF;
        color: #1E3A8A !important;
    }

    .wb-priority-low {
        background: #D1FAE5;
        color: #065F46 !important;
    }

    .wb-summary-card {
        background: #FFFFFF;
        border: 1px solid var(--wb-border);
        border-radius: 16px;
        padding: 0.7rem 0.95rem;
        font-size: 0.92rem;
        color: #334155 !important;
        box-shadow: 0 4px 14px rgba(7, 26, 45, 0.05);
    }

    .wb-summary-card * {
        color: #334155 !important;
        opacity: 1 !important;
    }

    .wb-summary-note {
        color: var(--wb-muted) !important;
        font-size: 0.8rem;
    }

    .wb-goal-card {
        background: #FFFFFF;
        border: 1px solid var(--wb-border);
        border-radius: 16px;
        padding: 0.9rem 1rem;
        margin-bottom: 0.7rem;
        box-shadow: 0 4px 14px rgba(7, 26, 45, 0.06);
    }

    .wb-goal-name {
        font-weight: 800;
        color: var(--wb-navy) !important;
    }

    .wb-goal-badge {
        float: right;
        border-radius: 999px;
        padding: 0.12rem 0.6rem;
        font-size: 0.72rem;
        font-weight: 800;
    }

    .wb-goal-ok {
        background: #ECFDF5;
        color: #065F46 !important;
    }

    .wb-goal-done {
        background: #D1FAE5;
        color: #065F46 !important;
    }

    .wb-goal-late {
        background: #FEF3C7;
        color: #92400E !important;
    }

    .wb-goal-bar {
        background: #E2E8F0;
        border-radius: 999px;
        height: 10px;
        margin: 0.5rem 0 0.4rem 0;
        overflow: hidden;
    }

    .wb-goal-fill {
        background: linear-gradient(90deg, #10B981, #34D399);
        height: 100%;
        border-radius: 999px;
    }

    .wb-goal-stats {
        color: var(--wb-muted) !important;
        font-size: 0.84rem;
    }

    /* Tighter vertical rhythm. */
    div[data-testid="stVerticalBlock"] {
        gap: 0.72rem !important;
    }

    hr {
        margin: 0.75rem 0 !important;
        border-color: rgba(100, 116, 139, 0.22) !important;
    }

    /* ============================================================
       Hero (product-style landing section at the top)
       ============================================================ */

    .wb-hero {
        background: linear-gradient(135deg, #FFFFFF 0%, #F0FDF7 100%);
        border: 1px solid var(--wb-border);
        border-radius: 20px;
        padding: 1.25rem 1.4rem 1.05rem 1.4rem;
        box-shadow: 0 6px 22px rgba(7, 26, 45, 0.07);
        margin-bottom: 0.35rem;
    }

    .wb-hero-kicker {
        display: flex;
        align-items: center;
        gap: 0.5rem;
        font-size: 0.82rem;
        font-weight: 800;
        color: var(--wb-emerald-dark) !important;
        letter-spacing: 0.05em;
        text-transform: uppercase;
        margin-bottom: 0.4rem;
    }

    .wb-hero-kicker img {
        border-radius: 9px;
    }

    .wb-hero-title {
        font-size: 2rem;
        font-weight: 850;
        color: var(--wb-navy) !important;
        line-height: 1.12;
        letter-spacing: -0.02em;
        margin: 0 0 0.3rem 0;
    }

    .wb-hero-sub {
        color: #3B4A5F !important;
        font-size: 1rem;
        line-height: 1.5;
        margin: 0 0 0.7rem 0;
        max-width: 36rem;
    }

    /* ============================================================
       Stat cards (custom metric cards with icon + helper text)
       ============================================================ */

    .wb-stat-grid {
        display: grid;
        grid-template-columns: repeat(auto-fit, minmax(155px, 1fr));
        gap: 0.7rem;
        margin: 0.2rem 0 0.4rem 0;
    }

    .wb-stat-card {
        background: linear-gradient(180deg, #FFFFFF 0%, #FBFDFF 100%);
        border: 1px solid var(--wb-border);
        border-radius: 16px;
        padding: 0.85rem 1rem 0.8rem 1rem;
        box-shadow: 0 4px 14px rgba(7, 26, 45, 0.07);
    }

    .wb-stat-icon {
        font-size: 1.1rem;
    }

    .wb-stat-label {
        color: var(--wb-muted) !important;
        font-size: 0.8rem;
        font-weight: 700;
        margin: 0.15rem 0 0.1rem 0;
    }

    .wb-stat-value {
        color: var(--wb-navy) !important;
        font-size: 1.55rem;
        font-weight: 850;
        line-height: 1.12;
        word-break: break-word;
    }

    .wb-stat-help {
        color: var(--wb-muted) !important;
        font-size: 0.75rem;
        line-height: 1.35;
        margin-top: 0.25rem;
    }

    /* ============================================================
       Intro cards (friendly page/section openers)
       ============================================================ */

    .wb-intro-card {
        background: linear-gradient(135deg, #FFFFFF 0%, #F0FDF7 100%);
        border: 1px solid var(--wb-border);
        border-left: 5px solid var(--wb-emerald);
        border-radius: 14px;
        padding: 0.75rem 1rem;
        color: #334155 !important;
        font-size: 0.94rem;
        line-height: 1.5;
        box-shadow: 0 3px 10px rgba(7, 26, 45, 0.05);
        margin-bottom: 0.4rem;
    }

    .wb-intro-title {
        font-weight: 800;
        color: var(--wb-navy) !important;
        margin-bottom: 0.1rem;
    }

    /* ============================================================
       Checklist items (recommended actions inside opportunity cards)
       ============================================================ */

    .wb-checklist {
        margin: 0.15rem 0 0.35rem 0;
    }

    .wb-check-item {
        display: flex;
        gap: 0.5rem;
        align-items: flex-start;
        background: #F8FAFC;
        border: 1px solid #EEF2F7;
        border-radius: 10px;
        padding: 0.45rem 0.65rem;
        margin-bottom: 0.35rem;
        font-size: 0.88rem;
        color: #334155 !important;
        line-height: 1.45;
    }

    .wb-check-mark {
        color: var(--wb-emerald-dark) !important;
        font-weight: 800;
        flex-shrink: 0;
    }

    /* ============================================================
       Ranked spending list rows
       ============================================================ */

    .wb-rank-row {
        display: flex;
        align-items: center;
        gap: 0.6rem;
        background: #FFFFFF;
        border: 1px solid #EEF2F7;
        border-radius: 12px;
        padding: 0.45rem 0.7rem;
        margin-bottom: 0.4rem;
    }

    .wb-rank-num {
        min-width: 1.7rem;
        height: 1.7rem;
        border-radius: 999px;
        background: var(--wb-mint);
        color: var(--wb-emerald-dark) !important;
        font-weight: 800;
        font-size: 0.8rem;
        display: inline-flex;
        align-items: center;
        justify-content: center;
        flex-shrink: 0;
    }

    .wb-rank-name {
        font-weight: 700;
        color: var(--wb-navy) !important;
        font-size: 0.92rem;
        flex: 1;
        min-width: 0;
    }

    .wb-rank-amount {
        font-weight: 800;
        color: var(--wb-navy) !important;
        font-size: 0.92rem;
        white-space: nowrap;
    }

    .wb-rank-share {
        color: var(--wb-muted) !important;
        font-size: 0.8rem;
        margin-left: 0.3rem;
    }

    /* ============================================================
       Education hub cards
       ============================================================ */

    .wb-edu-grid {
        display: grid;
        grid-template-columns: repeat(auto-fit, minmax(220px, 1fr));
        gap: 0.7rem;
        margin: 0.2rem 0 0.4rem 0;
    }

    .wb-edu-card {
        background: #FFFFFF;
        border: 1px solid var(--wb-border);
        border-radius: 16px;
        padding: 0.95rem 1rem;
        box-shadow: 0 4px 14px rgba(7, 26, 45, 0.05);
    }

    .wb-edu-icon {
        font-size: 1.35rem;
    }

    .wb-edu-title {
        font-weight: 800;
        color: var(--wb-navy) !important;
        margin: 0.25rem 0 0.15rem 0;
    }

    .wb-edu-text {
        color: #334155 !important;
        font-size: 0.9rem;
        line-height: 1.5;
    }

    /* Icon inside goal and action cards. */
    .wb-card-icon {
        font-size: 1.05rem;
        margin-right: 0.35rem;
    }

    /* ============================================================
       Mobile fixes
       ============================================================ */

    @media (max-width: 768px) {
        .block-container {
            padding-left: 1rem !important;
            padding-right: 1rem !important;
            /* Enough room so the demo banner never hides under the header
               bar that holds the sidebar arrow. */
            padding-top: 2.6rem !important;
            max-width: 100% !important;
        }

        /* App-like heading scale on phone: clear hierarchy without shouting. */
        h1 {
            font-size: 1.7rem !important;
            line-height: 1.15 !important;
        }

        h2 {
            font-size: 1.4rem !important;
            line-height: 1.2 !important;
        }

        h3 {
            font-size: 1.15rem !important;
            line-height: 1.25 !important;
        }

        .wb-header-title {
            font-size: 1.45rem !important;
        }

        .wb-hero {
            padding: 1rem 1.05rem 0.9rem 1.05rem !important;
        }

        .wb-hero-title {
            font-size: 1.5rem !important;
        }

        .wb-hero-sub {
            font-size: 0.93rem !important;
        }

        /* Stat cards: exactly two per row on phones - big enough to read,
           small enough to see the whole snapshot at a glance. */
        .wb-stat-grid {
            grid-template-columns: repeat(2, minmax(0, 1fr)) !important;
            gap: 0.55rem !important;
        }

        .wb-stat-value {
            font-size: 1.3rem !important;
        }

        .wb-edu-grid {
            grid-template-columns: 1fr !important;
        }

        .wb-header-sub {
            font-size: 0.95rem !important;
        }

        .wb-badge {
            font-size: 0.82rem !important;
            padding: 0.2rem 0.65rem !important;
        }

        .wb-demo-banner,
        .wb-disclaimer {
            font-size: 0.92rem !important;
            line-height: 1.5 !important;
        }

        /* One column on phone. It is less flashy, but it stops clipped/faded
           values in metrics and saving opportunity cards. */
        [data-testid="column"],
        [data-testid="stColumn"] {
            width: 100% !important;
            flex: 1 1 100% !important;
            min-width: 100% !important;
            margin-bottom: 0.45rem !important;
        }

        [data-testid="stMetric"] {
            min-height: auto !important;
            padding: 0.9rem 1rem !important;
        }

        [data-testid="stMetricValue"] {
            font-size: 1.55rem !important;
            line-height: 1.15 !important;
            white-space: normal !important;
            overflow: visible !important;
            text-overflow: clip !important;
        }

        [data-testid="stMetricLabel"] {
            font-size: 0.92rem !important;
        }

        .wb-action-card,
        .wb-goal-card,
        .wb-summary-card {
            padding: 0.85rem 0.9rem !important;
        }

        .wb-priority,
        .wb-goal-badge {
            float: none !important;
            display: inline-block !important;
            margin-top: 0.35rem !important;
        }

        [data-testid="stExpander"] summary {
            font-size: 0.95rem !important;
            line-height: 1.3 !important;
            padding: 0.75rem 0.85rem !important;
        }

        [data-testid="stExpander"] [data-testid="stMetricValue"] {
            font-size: 1.35rem !important;
        }

        .stButton > button,
        .stFormSubmitButton > button,
        .stDownloadButton > button {
            width: 100% !important;
            min-height: 48px !important;
        }

        [role="radiogroup"] {
            gap: 0.4rem !important;
        }

        [role="radiogroup"] label {
            margin-right: 0.35rem !important;
            font-size: 0.9rem !important;
        }

        [data-testid="stDataFrame"] {
            font-size: 0.85rem !important;
        }
    }
    </style>
    """, unsafe_allow_html=True)

inject_custom_css()

# Make sure the CSV files exist before anything tries to read them.
helpers.ensure_all_csv_files()


# ============================================================
# Small UI helpers
# ============================================================

def show_insight(insight_type, message):
    """Render a (type, message) insight tuple with the right Streamlit style."""
    if insight_type == "success":
        st.success(message)
    elif insight_type == "warning":
        st.warning(message)
    elif insight_type == "error":
        st.error(message)
    else:
        st.info(message)


def get_active_data():
    """
    Return (income, expenses, raw_goals) for the current mode.
    Demo Mode ON  -> realistic example data (real CSVs are never touched).
    Demo Mode OFF -> the user's real CSV data.
    """
    if st.session_state.get("demo_mode"):
        return helpers.get_demo_data()
    return helpers.load_income(), helpers.load_expenses(), helpers.load_goals()


def render_stat_cards(cards):
    """
    Custom metric cards: icon, label, a big value and a small helper line.
    A CSS grid keeps them four-across on desktop and two-across on phones
    without relying on Streamlit columns (which stack full-width on mobile
    and would make the snapshot very tall).

    `cards` is a list of dicts with keys: icon, label, value, help.
    All values here are app-generated (never raw user text), so they are safe
    to place in HTML.
    """
    boxes = "".join(
        '<div class="wb-stat-card">'
        f'<span class="wb-stat-icon">{card["icon"]}</span>'
        f'<div class="wb-stat-label">{card["label"]}</div>'
        f'<div class="wb-stat-value">{card["value"]}</div>'
        f'<div class="wb-stat-help">{card["help"]}</div>'
        '</div>'
        for card in cards
    )
    st.markdown(f'<div class="wb-stat-grid">{boxes}</div>', unsafe_allow_html=True)


# Icons for the Top 3 Money Actions cards, matched against the opportunity
# title. Purely visual - the rule engine in helpers.py is unchanged.
ACTION_ICONS = [
    ("food", "🛒"),
    ("subscription", "📺"),
    ("transport", "🚌"),
    ("energy", "⚡"),
    ("mobile", "📱"),
    ("phone", "📱"),
    ("broadband", "🌐"),
    ("internet", "🌐"),
    ("shopping", "🛍️"),
    ("entertainment", "🎬"),
    ("gym", "💪"),
    ("health", "💪"),
    ("education", "📚"),
]


def action_icon(title):
    """Pick a small icon for an action/opportunity title (fallback: 💡)."""
    lowered = str(title).lower()
    for word, icon in ACTION_ICONS:
        if word in lowered:
            return icon
    return "💡"


def render_top_actions(opportunities):
    """
    "Your Top 3 Money Actions": compact cards for the highest-impact non-debt
    opportunities - title, estimated monthly range, one next step, priority.
    """
    actions = helpers.top_saving_actions(opportunities, limit=3)
    if not actions:
        st.info("Add a few expenses and your top money actions will appear here.")
        return

    for action in actions:
        badge = (
            f'<span class="wb-priority wb-priority-{action["priority"].lower()}">'
            f'{action["priority"]}</span>'
        )
        icon = action_icon(action["short_title"])
        st.markdown(
            f'<div class="wb-action-card">'
            f'<div class="wb-action-title"><span class="wb-card-icon">{icon}</span>'
            f'{action["short_title"]} {badge}</div>'
            f'<div class="wb-action-saving">Est. £{action["monthly_low"]:,.2f} to '
            f'£{action["monthly_high"]:,.2f} / month</div>'
            f'<div class="wb-action-step">Next step: {action["next_step"]}</div>'
            f'</div>',
            unsafe_allow_html=True,
        )
    st.caption(
        "Estimated ranges only, not guaranteed savings. "
        "Debt repayment is shown separately as a potential interest reduction."
    )


# The user can choose how to view spending - different testers prefer
# different formats (ranked list stays the default).
SPENDING_VIEW_OPTIONS = ["Ranked list", "Percentages", "Bar chart", "Pie chart", "Table"]


def _figure_as_image(fig, width):
    """
    Render a matplotlib figure as a fixed-width image. This keeps charts
    compact instead of stretching to the full container, and images scale
    down automatically on small phone screens.
    """
    buffer = io.BytesIO()
    fig.savefig(buffer, format="png", dpi=150, bbox_inches="tight")
    plt.close(fig)
    st.image(buffer, width=width)


def render_spending_views(expenses_data, key_prefix):
    """
    Spending-by-category breakdown with a user-selectable view:
    ranked list (default), percentages, bar chart, pie chart, or table.
    `key_prefix` keeps widget keys unique when used on several pages.
    """
    totals = helpers.category_totals(expenses_data)
    if totals.empty:
        st.write("No expenses recorded for this period yet.")
        return

    # Everything lives in one bordered card so the selector and the chosen
    # view read as a single, tidy unit.
    with st.container(border=True):
        st.caption("Choose the view that makes your spending easiest to understand.")
        choice = st.radio(
            "Choose spending view",
            SPENDING_VIEW_OPTIONS,
            horizontal=True,
            key=f"spending_view_{key_prefix}",
            label_visibility="collapsed",
        )
        total_spent = float(totals.sum())

        if choice == "Ranked list":
            rows = []
            for rank, (category, amount) in enumerate(totals.items(), start=1):
                share = (amount / total_spent * 100) if total_spent > 0 else 0
                rows.append(
                    '<div class="wb-rank-row">'
                    f'<span class="wb-rank-num">{rank}</span>'
                    f'<span class="wb-rank-name">{html.escape(str(category))}</span>'
                    f'<span class="wb-rank-amount">£{amount:,.2f}'
                    f'<span class="wb-rank-share">{share:.1f}%</span></span>'
                    '</div>'
                )
            st.markdown("".join(rows), unsafe_allow_html=True)

        elif choice == "Percentages":
            for category, amount in totals.items():
                share = (amount / total_spent * 100) if total_spent > 0 else 0
                st.write(f"**{category}** - {share:.1f}% of spending")
                st.progress(min(100, int(round(share))))

        elif choice == "Bar chart":
            # Horizontal bars: category names stay readable and the biggest
            # spender sits at the top.
            ordered = totals.sort_values(ascending=True)  # barh draws bottom-up
            fig, ax = plt.subplots(figsize=(6.2, 0.36 * len(ordered) + 0.7))
            bars = ax.barh(ordered.index, ordered.values, color="#10B981")
            ax.bar_label(bars, fmt="£%.0f", fontsize=7, padding=3, color="#3B4A5F")
            ax.set_xlabel("£ spent", fontsize=8)
            ax.tick_params(labelsize=8)
            ax.margins(x=0.12)
            ax.spines["top"].set_visible(False)
            ax.spines["right"].set_visible(False)
            ax.xaxis.grid(True, color="#E5EAF1")
            ax.set_axisbelow(True)
            _figure_as_image(fig, width=560)

        elif choice == "Pie chart":
            # Compact pie: percentages inside the slices (hidden below 3% to
            # avoid clutter) and category names in a small legend beside it.
            fig, ax = plt.subplots(figsize=(3.4, 3.4))
            wedges, _, _ = ax.pie(
                totals.values,
                autopct=lambda pct: f"{pct:.0f}%" if pct >= 3 else "",
                startangle=90,
                textprops={"fontsize": 7, "color": "white", "fontweight": "bold"},
            )
            ax.legend(
                wedges,
                list(totals.index),
                loc="center left",
                bbox_to_anchor=(1.0, 0.5),
                fontsize=7,
                frameon=False,
            )
            ax.axis("equal")
            _figure_as_image(fig, width=440)

        else:  # Table
            breakdown = helpers.category_breakdown_table(expenses_data)
            st.dataframe(
                breakdown,
                width="stretch",
                hide_index=True,
                column_config={
                    "Amount": st.column_config.NumberColumn("Amount", format="£%.2f"),
                    "Share %": st.column_config.NumberColumn("Share %", format="%.1f%%"),
                },
            )


def render_saving_opportunities(
    opportunities,
    ai_ready,
    ai_message,
    ollama_host,
    ollama_model,
    summary,
    period_label,
    page_key,
    amount_label="Current monthly amount",
):
    """
    Render the "Smart Saving Opportunities" section from a list of opportunity
    dictionaries (see helpers.generate_saving_opportunities). Shows a summary
    box, then each opportunity as an expandable card with its figures, why it
    matters, rule-based actions, a clear "estimate, not a guarantee" disclaimer,
    and a button to generate an optional AI saving plan.

    The rule-based content always renders. The AI plan is only generated when the
    user clicks the per-card button (never automatically), and the result is
    cached in session state so it stays visible without re-calling the model.

    Parameters:
      ai_ready / ai_message    - local AI status from ai_helper.check_status
      ollama_host / ollama_model - which local model to call
      summary                  - dict from helpers.compute_summary (AI context)
      period_label             - e.g. the selected month, or "All time"
      page_key                 - short id ("dashboard"/"insights") for unique keys
      amount_label             - names the headline amount (varies by page/period)
    """
    if not opportunities:
        st.info("No major saving opportunities detected for this period yet.")
        return

    # ---- Compact summary card (above the cards) ----
    totals = helpers.summarise_saving_opportunities(opportunities)
    count = totals["count"]
    headline = f"<b>{count} saving opportunit{'y' if count == 1 else 'ies'} detected.</b>"
    if totals["saving_count"] > 0:
        # Debt repayment is never summed in: we have no interest-rate/APR data
        # to estimate a real interest saving, so the totals exclude it.
        ranges = (
            f" Est. total: <b>£{totals['total_monthly_low']:,.2f} to "
            f"£{totals['total_monthly_high']:,.2f}/month</b> "
            f"(£{totals['total_yearly_low']:,.0f} to £{totals['total_yearly_high']:,.0f}/year)."
        )
    else:
        ranges = " No bill or spending savings to total yet."
    st.markdown(
        f'<div class="wb-summary-card">{headline}{ranges}<br>'
        f'<span class="wb-summary-note">Estimates only, not guaranteed savings. '
        f'Excludes debt repayment unless interest-rate data is available.</span></div>',
        unsafe_allow_html=True,
    )

    for index, opp in enumerate(opportunities):
        # Unique keys per page/card so buttons and cached AI plans never clash.
        plan_key = f"ai_saving_plan_{page_key}_{index}_{opp['title']}"
        cache_key = f"{plan_key}__{opp['current_amount']}__text"

        # Open the top (highest-priority) card by default, and keep open any card
        # whose AI plan has already been generated (so the cached plan stays
        # visible); the rest stay collapsed to keep things tidy.
        expanded = (index == 0) or bool(st.session_state.get(cache_key))
        with st.expander(
            f"{opp['title']}  (Priority: {opp['priority']})",
            expanded=expanded,
        ):
            st.caption(f"Detected from: {opp['detected_from']}")

            # Headline spend on its own row so the value never gets clipped.
            st.metric(amount_label, f"£{opp['current_amount']:,.2f}")

            # Debt is shown as a long-term interest reduction, not a normal bill
            # saving, so its two figures are relabelled accordingly.
            if opp.get("saving_kind") == "interest":
                monthly_saving_label = "Potential monthly interest reduction"
                yearly_saving_label = "Potential yearly interest reduction"
            else:
                monthly_saving_label = "Estimated monthly saving"
                yearly_saving_label = "Estimated yearly saving"

            # The two ranges share a roomy two-column row. (Three columns made
            # these longer values overflow / truncate inside the card.)
            saving_col1, saving_col2 = st.columns(2)
            saving_col1.metric(
                monthly_saving_label,
                f"£{opp['estimated_monthly_saving_low']:,.2f} to "
                f"£{opp['estimated_monthly_saving_high']:,.2f}",
            )
            saving_col2.metric(
                yearly_saving_label,
                f"£{opp['estimated_yearly_saving_low']:,.2f} to "
                f"£{opp['estimated_yearly_saving_high']:,.2f}",
            )

            # Priority already shows in the card title, so no big alert box
            # here - keeps the expanded card compact.
            st.markdown(f"**Why it matters:** {opp['why_it_matters']}")

            # These come from the rule engine (helpers), not the AI model.
            # Rendered as tick-style checklist items so they read as a to-do
            # list rather than a wall of bullets.
            st.markdown("**Recommended actions**")
            checklist = "".join(
                '<div class="wb-check-item"><span class="wb-check-mark">✓</span>'
                f'<span>{html.escape(str(step))}</span></div>'
                for step in opp["action_steps"]
            )
            st.markdown(
                f'<div class="wb-checklist">{checklist}</div>',
                unsafe_allow_html=True,
            )

            # ---- Optional AI saving plan (only runs when the user clicks) ----
            if st.button("Generate AI saving plan", key=plan_key):
                if not ai_ready:
                    base = (
                        "Local AI (Ollama) isn't connected, so an AI saving plan "
                        "can't be generated right now. The rule-based tips above "
                        "still apply."
                    )
                    st.info(f"{ai_message} {base}" if ai_message else base)
                else:
                    st.markdown("**AI saving plan**")
                    client = ai_helper.get_client(ollama_host)
                    plan_text = st.write_stream(
                        ai_helper.stream_saving_opportunity_advice(
                            client,
                            ollama_model,
                            opp,
                            budget_summary=summary,
                            period_label=period_label,
                        )
                    )
                    # Cache so the plan stays visible on later reruns (no re-call).
                    st.session_state[cache_key] = plan_text
            elif st.session_state.get(cache_key):
                st.markdown("**AI saving plan**")
                st.write(st.session_state[cache_key])

            st.caption(opp["disclaimer"])


# ============================================================
# Navigation state (shared by the sidebar and the in-page App menu)
# ============================================================
#
# On phones the Streamlit sidebar can be collapsed (or hard to reopen), so the
# app offers navigation in TWO places: the normal sidebar AND an "App menu"
# expander at the top of the main page. Both write to the same session-state
# values, so they always stay in sync:
#   st.session_state["current_page"] - the page being shown (single source of truth)
#   st.session_state["demo_mode"]    - whether Demo Mode is on (single source of truth)
# Each widget has its own key; before it renders we copy the master value into
# the widget's key, and when the user changes it, on_change copies the widget's
# value back into the master. Changing either control updates both.

PAGES = [
    "Dashboard",
    "Add Income",
    "Add Expense",
    "WiseBudget AI Coach",
    "Savings Goals",
    "Investment Learning Hub",
    "Feedback",
]

# This public cloud demo starts with Demo Mode ON, so visitors always see
# example data first and never need to enter anything.
if "current_page" not in st.session_state:
    st.session_state["current_page"] = PAGES[0]
if "demo_mode" not in st.session_state:
    st.session_state["demo_mode"] = True


def sync_current_page(widget_key):
    """Copy a navigation widget's value into the master current_page value."""
    st.session_state["current_page"] = st.session_state[widget_key]


def sync_demo_mode(widget_key):
    """Copy a Demo Mode widget's value into the master demo_mode value."""
    st.session_state["demo_mode"] = st.session_state[widget_key]


DEMO_MODE_HELP = (
    "Show realistic example data instead of your real records. Your CSV files "
    "are never changed. On in this public demo by default."
)


# ============================================================
# Sidebar: navigation + AI settings
# ============================================================

# Compact brand row: small icon + name side by side.
with st.sidebar:
    if ICON_FILE.exists():
        brand_icon, brand_name = st.columns([1, 3], vertical_alignment="center")
        brand_icon.image(str(ICON_FILE), width=42)
        brand_name.markdown(
            '<span class="wb-side-name">WiseBudget AI</span>', unsafe_allow_html=True
        )
    else:
        st.title("WiseBudget AI")

# Demo Mode: shows realistic example data everywhere without ever touching
# the real CSV files.
st.session_state["demo_mode_sidebar"] = st.session_state["demo_mode"]
st.sidebar.toggle(
    "Demo Mode",
    key="demo_mode_sidebar",
    on_change=sync_demo_mode,
    args=("demo_mode_sidebar",),
    help=DEMO_MODE_HELP,
)
if st.session_state["demo_mode"]:
    st.sidebar.caption("🧪 Example data only - your files are untouched.")

st.session_state["nav_sidebar"] = st.session_state["current_page"]
st.sidebar.radio(
    "Navigation",
    PAGES,
    key="nav_sidebar",
    on_change=sync_current_page,
    args=("nav_sidebar",),
)

st.sidebar.write("---")

with st.sidebar.expander("⚙️ AI Settings", expanded=False):
    st.write(
        "AI features run on a local **Ollama** model — free, private and offline. "
        "Install Ollama from [ollama.com](https://ollama.com), then pull a model "
        "(in a terminal: `ollama pull llama3.2`)."
    )
    st.caption(
        "In this public cloud demo there is usually no local AI available, so "
        "the app runs in rule-based mode - all insights and saving "
        "opportunities still work."
    )
    ollama_model = st.text_input(
        "Ollama model",
        value=st.session_state.get("ollama_model", ai_helper.DEFAULT_MODEL),
        help="The name of a model you've pulled with Ollama, e.g. llama3.2, llama3.1, mistral, qwen2.5.",
    )
    st.session_state["ollama_model"] = ollama_model
    ollama_host = st.text_input(
        "Ollama address",
        value=st.session_state.get("ollama_host", ai_helper.DEFAULT_HOST),
        help="Leave this as-is unless you run Ollama on another machine or port.",
    )
    st.session_state["ollama_host"] = ollama_host

ollama_model = st.session_state.get("ollama_model", ai_helper.DEFAULT_MODEL)
ollama_host = st.session_state.get("ollama_host", ai_helper.DEFAULT_HOST)
ai_ready, ai_message = ai_helper.check_status(ollama_host, ollama_model)

# AI status as a small branded pill: green = connected, amber = rule-based.
if ai_ready:
    st.sidebar.markdown(
        '<span class="wb-ai-pill wb-ai-on">● Local AI connected</span>',
        unsafe_allow_html=True,
    )
else:
    st.sidebar.markdown(
        '<span class="wb-ai-pill wb-ai-off">● Rule-based mode</span>',
        unsafe_allow_html=True,
    )
    st.sidebar.caption(ai_message)


# ============================================================
# App header
# ============================================================

# Demo Mode label sits above everything so testers always know what they see.
if st.session_state.get("demo_mode"):
    st.markdown(
        '<div class="wb-demo-banner">🧪 Demo Mode: using example data only</div>',
        unsafe_allow_html=True,
    )

# Hero: product-style landing section. The small logo is embedded as a data
# URI so it can live inside the card's HTML (st.image can't be nested there).
if ICON_FILE.exists():
    _icon_b64 = base64.b64encode(ICON_FILE.read_bytes()).decode()
    hero_logo = f'<img src="data:image/png;base64,{_icon_b64}" width="34" alt="">'
else:
    hero_logo = "💷"

st.markdown(
    f'<div class="wb-hero">'
    f'<div class="wb-hero-kicker">{hero_logo} WiseBudget AI</div>'
    f'<p class="wb-hero-title">Take control of your spending</p>'
    f'<p class="wb-hero-sub">Track your money, spot saving opportunities, '
    f'and learn better financial habits.</p>'
    f'<span class="wb-badge">🔒 Local-first</span>'
    f'<span class="wb-badge">🎓 Education only</span>'
    f'<span class="wb-badge">≈ Estimates, not guarantees</span>'
    f'</div>',
    unsafe_allow_html=True,
)

st.markdown(
    '<div class="wb-disclaimer">This app is for budgeting and financial education only. '
    'It does not provide personal financial advice or tell users what to buy, sell, or invest in.</div>',
    unsafe_allow_html=True,
)

# Cloud-demo privacy note: this public version runs on shared hosting, so
# testers should never type real financial details into it.
st.markdown(
    '<div class="wb-disclaimer">🔒 This public demo is for testing the interface only. '
    'Do not enter private financial information.</div>',
    unsafe_allow_html=True,
)


# ============================================================
# App menu: mobile-safe navigation fallback
# ============================================================
# Mirrors the sidebar controls inside the main page, so phones can always
# navigate and toggle Demo Mode even when the sidebar is collapsed.

with st.expander("📱 App menu", expanded=False):
    st.caption("Use this menu if the sidebar is hidden on mobile.")

    st.session_state["demo_mode_menu"] = st.session_state["demo_mode"]
    st.toggle(
        "Demo Mode",
        key="demo_mode_menu",
        on_change=sync_demo_mode,
        args=("demo_mode_menu",),
        help=DEMO_MODE_HELP,
    )

    st.session_state["nav_menu"] = st.session_state["current_page"]
    st.selectbox(
        "Go to page",
        PAGES,
        key="nav_menu",
        on_change=sync_current_page,
        args=("nav_menu",),
    )

    if ai_ready:
        st.markdown(
            '<span class="wb-ai-pill wb-ai-on">● Local AI connected</span>',
            unsafe_allow_html=True,
        )
    else:
        st.markdown(
            '<span class="wb-ai-pill wb-ai-off">● Rule-based mode</span>',
            unsafe_allow_html=True,
        )


# The rest of the app routes on this one value, which both the sidebar radio
# and the App menu selector control.
page = st.session_state["current_page"]


# ============================================================
# Dashboard page
# ============================================================

if page == "Dashboard":
    st.header("Dashboard")

    income_data, expenses_data, goals_raw = get_active_data()
    goals_data = helpers.prepare_goals_data(goals_raw)

    # ---- Period filter ----
    month_options = helpers.get_month_options(income_data, expenses_data)
    selected_month = st.selectbox("Period", month_options)

    income_view = helpers.filter_by_month(income_data, selected_month)
    expenses_view = helpers.filter_by_month(expenses_data, selected_month)

    summary = helpers.compute_summary(income_view, expenses_view)

    render_stat_cards([
        {"icon": "💷", "label": "Total Income",
         "value": f"£{summary['total_income']:,.2f}",
         "help": "Income recorded for this period"},
        {"icon": "🧾", "label": "Total Expenses",
         "value": f"£{summary['total_expenses']:,.2f}",
         "help": "Spending recorded for this period"},
        {"icon": "💰", "label": "Remaining Balance",
         "value": f"£{summary['remaining_balance']:,.2f}",
         "help": "Income minus expenses"},
        {"icon": "📈", "label": "Savings Rate",
         "value": f"{summary['savings_rate']:.1f}%",
         "help": "Money kept after living costs"},
    ])

    st.write("---")

    # ---- Your Top 3 Money Actions (highest-impact, non-debt) ----
    st.subheader("Your Top 3 Money Actions")
    # "All time" spans several months, so estimates use the monthly AVERAGE
    # rather than pretending the total is one month's spending.
    if selected_month == ALL_TIME:
        months_covered = helpers.count_months_covered(expenses_view)
    else:
        months_covered = 1
    saving_opportunities = helpers.generate_saving_opportunities(
        expenses_view, income_view, months_covered=months_covered
    )
    render_top_actions(saving_opportunities)

    st.write("---")

    # ---- Smart Saving Opportunities (selected period only) ----
    st.subheader("Smart Saving Opportunities")
    st.caption(f"Based on your expenses for: {selected_month}")
    if months_covered > 1:
        st.caption(f"Amounts are monthly averages across {months_covered} months of data.")
        amount_label = "Average monthly amount based on selected data"
    else:
        amount_label = "Current monthly amount"
    render_saving_opportunities(
        saving_opportunities,
        ai_ready=ai_ready,
        ai_message=ai_message,
        ollama_host=ollama_host,
        ollama_model=ollama_model,
        summary=summary,
        period_label=selected_month,
        page_key="dashboard",
        amount_label=amount_label,
    )

    st.write("---")

    st.subheader("Spending by Category")
    render_spending_views(expenses_view, key_prefix="dashboard")

    st.write("---")

    st.subheader("Income vs Expenses by Month")
    with st.container(border=True):
        trend = helpers.monthly_totals(income_data, expenses_data)
        if trend.empty:
            st.write("Not enough data yet to show a monthly breakdown.")
        else:
            # Monthly figures as a simple table (newest first) instead of a chart.
            trend_table = trend.reset_index()
            trend_table.columns = ["Month"] + list(trend_table.columns[1:])
            trend_table["Net"] = trend_table["Income"] - trend_table["Expenses"]
            trend_table = trend_table.sort_values("Month", ascending=False)
            st.dataframe(
                trend_table,
                width="stretch",
                hide_index=True,
                column_config={
                    "Income": st.column_config.NumberColumn("Income", format="£%.2f"),
                    "Expenses": st.column_config.NumberColumn("Expenses", format="£%.2f"),
                    "Net": st.column_config.NumberColumn("Net", format="£%.2f"),
                },
            )

    st.write("---")

    st.subheader("Savings Goals Overview")
    if goals_data.empty:
        st.write("No savings goals recorded yet.")
    else:
        # Each goal is a compact card: name, status badge, progress bar and
        # the key figures on one line.
        for _, goal in goals_data.iterrows():
            progress = float(goal["progress_percentage"])
            if goal.get("is_overdue"):
                badge = '<span class="wb-goal-badge wb-goal-late">Deadline passed</span>'
            elif progress >= 100:
                badge = '<span class="wb-goal-badge wb-goal-done">Complete</span>'
            else:
                badge = '<span class="wb-goal-badge wb-goal-ok">In progress</span>'

            goal_name = html.escape(str(goal["goal_name"]))
            st.markdown(
                f'<div class="wb-goal-card">'
                f'<div><span class="wb-card-icon">🎯</span>'
                f'<span class="wb-goal-name">{goal_name}</span>{badge}</div>'
                f'<div class="wb-goal-bar">'
                f'<div class="wb-goal-fill" style="width:{min(100.0, progress):.0f}%"></div></div>'
                f'<div class="wb-goal-stats">'
                f'Saved £{goal["current_amount"]:,.2f} of £{goal["target_amount"]:,.2f} '
                f'({progress:.1f}%) - £{goal["remaining_amount"]:,.2f} remaining - '
                f'deadline {goal["deadline"]}</div>'
                f'</div>',
                unsafe_allow_html=True,
            )

    st.write("---")

    st.subheader("Records & export")
    st.caption("The detailed data behind the dashboard - open it when you need it.")

    # Collapsed by default so the dashboard stays focused on insights.
    with st.expander(f"View detailed records ({selected_month})", expanded=False):
        st.write("**Income** (highest first)")
        # Display-only sort: biggest amounts at the top. The stored CSV order is
        # untouched (editing/deleting still happens on the Add pages).
        income_ranked = income_view.sort_values("amount", ascending=False).reset_index(drop=True)
        st.dataframe(income_ranked, width="stretch")
        st.write("**Expenses** (highest first)")
        expenses_ranked = expenses_view.sort_values("amount", ascending=False).reset_index(drop=True)
        st.dataframe(expenses_ranked, width="stretch")

        st.markdown("**Export your data**")
        exp1, exp2, exp3 = st.columns(3)
        exp1.download_button(
            "⬇️ Income CSV",
            helpers.dataframe_to_csv_bytes(income_data),
            "income.csv",
            "text/csv",
            width="stretch",
        )
        exp2.download_button(
            "⬇️ Expenses CSV",
            helpers.dataframe_to_csv_bytes(expenses_data),
            "expenses.csv",
            "text/csv",
            width="stretch",
        )
        exp3.download_button(
            "⬇️ Goals CSV",
            helpers.dataframe_to_csv_bytes(goals_raw),
            "goals.csv",
            "text/csv",
            width="stretch",
        )


# ============================================================
# Add Income page
# ============================================================

elif page == "Add Income":
    st.header("Add Income")

    # Demo Mode shows example data, so adding/editing real records is paused
    # to avoid any confusion between demo rows and the user's own files.
    if st.session_state.get("demo_mode"):
        st.info("🧪 Demo Mode is active. Turn it off to add your own records.")
        st.caption("The Demo Mode toggle is in the sidebar and the App menu at the top.")
        st.stop()

    st.markdown(
        '<div class="wb-intro-card">'
        '<div class="wb-intro-title">Record money coming in.</div>'
        'Salary, tips, freelance income, benefits, or anything else you receive.'
        '</div>',
        unsafe_allow_html=True,
    )

    with st.form("income_form"):
        income_date = st.date_input("Income date", value=date.today())
        income_source = st.text_input("Income source", placeholder="Example: Salary")
        income_amount = st.number_input(
            "Income amount (£)", min_value=0.0, value=0.0, step=10.0
        )
        submitted = st.form_submit_button("Save Income")

        if submitted:
            if income_source.strip() == "":
                st.error("Please enter an income source.")
            elif income_amount <= 0:
                st.error("Please enter an amount greater than 0.")
            else:
                income_data = helpers.load_income()
                new_income = pd.DataFrame(
                    {
                        "date": [income_date.strftime("%Y-%m-%d")],
                        "source": [income_source.strip()],
                        "amount": [income_amount],
                    }
                )
                income_data = pd.concat([income_data, new_income], ignore_index=True)
                helpers.save_csv(income_data, INCOME_FILE)
                st.success("Income saved successfully.")

    st.write("---")
    st.subheader("Edit or delete income records")
    st.caption("Edit cells directly, or use the 🗑 / + controls to delete or add rows, then save.")

    income_data = helpers.load_income()
    edited_income = st.data_editor(
        income_data,
        num_rows="dynamic",
        width="stretch",
        key="income_editor",
        column_config={
            "date": st.column_config.TextColumn("Date", help="YYYY-MM-DD"),
            "source": st.column_config.TextColumn("Source"),
            "amount": st.column_config.NumberColumn("Amount (£)", min_value=0.0, step=10.0, format="£%.2f"),
        },
    )

    if st.button("💾 Save income changes"):
        cleaned = helpers.clean_edited_table(edited_income, key_field="source")
        helpers.save_csv(cleaned, INCOME_FILE)
        st.success("Income records updated.")
        st.rerun()


# ============================================================
# Add Expense page
# ============================================================

elif page == "Add Expense":
    st.header("Add Expense")

    # Same demo-mode guard as Add Income (see comment there).
    if st.session_state.get("demo_mode"):
        st.info("🧪 Demo Mode is active. Turn it off to add your own records.")
        st.caption("The Demo Mode toggle is in the sidebar and the App menu at the top.")
        st.stop()

    st.markdown(
        '<div class="wb-intro-card">'
        '<div class="wb-intro-title">Track spending and categorise it automatically.</div>'
        'Pick a category yourself, or choose Auto Detect and WiseBudget AI '
        'categorises the expense from its description.'
        '</div>',
        unsafe_allow_html=True,
    )

    categories = ["Auto Detect"] + EXPENSE_CATEGORIES

    with st.form("expense_form"):
        expense_date = st.date_input("Expense date", value=date.today())
        expense_description = st.text_input(
            "Expense description", placeholder="Example: Tesco shopping"
        )
        expense_amount = st.number_input(
            "Expense amount (£)", min_value=0.0, value=0.0, step=5.0
        )
        expense_category = st.selectbox("Expense category", categories)
        submitted = st.form_submit_button("Save Expense")

        if submitted:
            if expense_description.strip() == "":
                st.error("Please enter an expense description.")
            elif expense_amount <= 0:
                st.error("Please enter an amount greater than 0.")
            else:
                if expense_category == "Auto Detect":
                    final_category = helpers.auto_categorise_expense(expense_description)
                else:
                    final_category = expense_category

                expenses_data = helpers.load_expenses()
                new_expense = pd.DataFrame(
                    {
                        "date": [expense_date.strftime("%Y-%m-%d")],
                        "description": [expense_description.strip()],
                        "amount": [expense_amount],
                        "category": [final_category],
                    }
                )
                expenses_data = pd.concat([expenses_data, new_expense], ignore_index=True)
                helpers.save_csv(expenses_data, EXPENSES_FILE)
                st.success(f"Expense saved successfully. Category: {final_category}")

    st.write("---")
    st.subheader("Edit or delete expense records")
    st.caption("Edit cells directly, or use the 🗑 / + controls to delete or add rows, then save.")

    expenses_data = helpers.load_expenses()
    edited_expenses = st.data_editor(
        expenses_data,
        num_rows="dynamic",
        width="stretch",
        key="expense_editor",
        column_config={
            "date": st.column_config.TextColumn("Date", help="YYYY-MM-DD"),
            "description": st.column_config.TextColumn("Description"),
            "amount": st.column_config.NumberColumn("Amount (£)", min_value=0.0, step=5.0, format="£%.2f"),
            "category": st.column_config.SelectboxColumn("Category", options=EXPENSE_CATEGORIES),
        },
    )

    if st.button("💾 Save expense changes"):
        cleaned = helpers.clean_edited_table(edited_expenses, key_field="description", has_category=True)
        helpers.save_csv(cleaned, EXPENSES_FILE)
        st.success("Expense records updated.")
        st.rerun()


# ============================================================
# WiseBudget AI Coach page
# (merges the old "AI Budget Insights" and "Ask WiseBudget AI" pages)
# ============================================================

elif page == "WiseBudget AI Coach":
    st.header("WiseBudget AI Coach")

    st.markdown(
        '<div class="wb-intro-card">'
        '<div class="wb-intro-title">Your personal budgeting coach</div>'
        'Ask WiseBudget AI about your spending, goals, and saving opportunities.'
        '</div>',
        unsafe_allow_html=True,
    )

    # AI status pill (same styling as the sidebar one). Rule-based mode is a
    # designed state, not an error - the wording reflects that.
    if ai_ready:
        st.markdown(
            '<span class="wb-ai-pill wb-ai-on">● Local AI connected</span>',
            unsafe_allow_html=True,
        )
    else:
        st.markdown(
            '<span class="wb-ai-pill wb-ai-off">● Rule-based mode active</span>',
            unsafe_allow_html=True,
        )
        st.caption(
            "Rule-based mode active — smart checks and saving opportunities "
            "still work."
        )

    # One shared data pass for every section on this page. Analyses ALL
    # expenses, so estimates are normalised to a monthly average.
    income_data, expenses_data, goals_raw = get_active_data()
    goals_data = helpers.prepare_goals_data(goals_raw)
    summary = helpers.compute_summary(income_data, expenses_data)
    totals = helpers.category_totals(expenses_data)
    months_covered = helpers.count_months_covered(expenses_data)
    saving_opportunities = helpers.generate_saving_opportunities(
        expenses_data, income_data, months_covered=months_covered
    )

    # The chat and the one-click analysis share this context, so the AI always
    # sees the same numbers the page shows (incl. saving opportunities).
    ai_context = ai_helper.build_financial_context(
        summary, totals, goals_data, period_label="All time",
        saving_opportunities=saving_opportunities,
    )

    st.write("---")

    # ---- Budget snapshot ----
    st.subheader("Budget snapshot")
    render_stat_cards([
        {"icon": "💷", "label": "Total Income",
         "value": f"£{summary['total_income']:,.2f}",
         "help": "All income recorded"},
        {"icon": "🧾", "label": "Total Expenses",
         "value": f"£{summary['total_expenses']:,.2f}",
         "help": "All spending recorded"},
        {"icon": "💰", "label": "Remaining Balance",
         "value": f"£{summary['remaining_balance']:,.2f}",
         "help": "Income minus expenses"},
        {"icon": "📈", "label": "Savings Rate",
         "value": f"{summary['savings_rate']:.1f}%",
         "help": "Money kept after living costs"},
    ])

    st.write("---")

    # ---- Quick checks (rule-based, always work without AI) ----
    st.subheader("Quick checks")
    with st.container(border=True):
        insights = helpers.generate_budget_insights(
            summary["total_income"],
            summary["total_expenses"],
            summary["remaining_balance"],
            summary["savings_rate"],
            expenses_data,
        )
        for insight_type, message in insights:
            show_insight(insight_type, message)

    st.write("---")

    # ---- Smart Saving Opportunities ----
    st.subheader("Smart Saving Opportunities")
    if months_covered > 1:
        st.caption(f"Amounts are monthly averages across {months_covered} months of data.")
        coach_amount_label = "Average monthly amount based on selected data"
    else:
        coach_amount_label = "Current monthly amount"
    render_saving_opportunities(
        saving_opportunities,
        ai_ready=ai_ready,
        ai_message=ai_message,
        ollama_host=ollama_host,
        ollama_model=ollama_model,
        summary=summary,
        period_label="All time",
        page_key="coach",
        amount_label=coach_amount_label,
    )

    st.write("---")

    # ---- One-click AI analysis ----
    st.subheader("✨ AI budget analysis")
    with st.container(border=True):
        if not ai_ready:
            st.info(
                "Rule-based mode active — smart checks and saving opportunities "
                "still work. Connecting a local Ollama model enables this "
                "optional AI analysis."
            )
        elif summary["total_income"] <= 0:
            st.warning("Add some income first so the AI has something to analyse.")
        else:
            st.caption("One click, and the local AI reviews your whole budget.")
            client = ai_helper.get_client(ollama_host)
            if st.button("Generate AI budget analysis"):
                with st.chat_message("assistant"):
                    st.write_stream(ai_helper.stream_insights(client, ollama_model, ai_context))

    st.write("---")

    # ---- Chat assistant ----
    st.subheader("💬 Chat with WiseBudget AI")
    if not ai_ready:
        st.info(
            "Rule-based mode active — smart checks and saving opportunities "
            "still work. The chat assistant needs a local Ollama model, which "
            "isn't available in this cloud demo."
        )
    else:
        client = ai_helper.get_client(ollama_host)

        if "chat_messages" not in st.session_state:
            st.session_state["chat_messages"] = []

        # One card holds the whole conversation: suggestions, history and the
        # input box (st.chat_input renders inline inside a container).
        with st.container(border=True):
            # Beginner-friendly prompt suggestions: one click asks the question.
            st.caption("Try asking:")
            suggestions = [
                "Where am I overspending?",
                "Which saving opportunity should I review first?",
                "Explain my savings rate",
                "How can I reduce subscriptions?",
                "What should I focus on this month?",
            ]
            suggestion_cols = st.columns(len(suggestions))
            clicked_suggestion = None
            for index, (suggestion_col, suggestion) in enumerate(zip(suggestion_cols, suggestions)):
                if suggestion_col.button(suggestion, key=f"coach_suggestion_{index}"):
                    clicked_suggestion = suggestion

            if st.button("🧹 Clear chat"):
                st.session_state["chat_messages"] = []
                st.rerun()

            # Replay history.
            for message in st.session_state["chat_messages"]:
                with st.chat_message(message["role"]):
                    st.write(message["content"])

            prompt = st.chat_input("e.g. How can I boost my savings rate?")
            if clicked_suggestion:
                prompt = clicked_suggestion

            if prompt:
                st.session_state["chat_messages"].append({"role": "user", "content": prompt})
                with st.chat_message("user"):
                    st.write(prompt)

                with st.chat_message("assistant"):
                    reply = st.write_stream(
                        ai_helper.stream_chat(client, ollama_model, ai_context, st.session_state["chat_messages"])
                    )
                st.session_state["chat_messages"].append({"role": "assistant", "content": reply})


# ============================================================
# Savings Goals page
# ============================================================

elif page == "Savings Goals":
    st.header("Savings Goals")

    st.markdown(
        '<div class="wb-intro-card">'
        '<div class="wb-intro-title">Save towards what matters.</div>'
        'Create savings goals and track your progress towards them.'
        '</div>',
        unsafe_allow_html=True,
    )

    if st.session_state.get("demo_mode"):
        st.info("🧪 Demo Mode is active. Turn it off to add your own goals.")
    else:
        with st.form("goals_form"):
            goal_name = st.text_input("Goal name", placeholder="Example: Emergency Fund")
            target_amount = st.number_input("Target amount (£)", min_value=0.0, value=0.0, step=50.0)
            current_amount = st.number_input("Current saved amount (£)", min_value=0.0, value=0.0, step=25.0)
            deadline = st.date_input("Goal deadline", value=date.today())
            submitted = st.form_submit_button("Save Goal")

            if submitted:
                if goal_name.strip() == "":
                    st.error("Please enter a goal name.")
                elif target_amount <= 0:
                    st.error("Please enter a target amount greater than 0.")
                elif current_amount > target_amount:
                    st.error("Current saved amount cannot be greater than target amount.")
                else:
                    goals_data = helpers.load_goals()
                    new_goal = pd.DataFrame(
                        {
                            "goal_name": [goal_name.strip()],
                            "target_amount": [target_amount],
                            "current_amount": [current_amount],
                            "deadline": [deadline.strftime("%Y-%m-%d")],
                        }
                    )
                    goals_data = pd.concat([goals_data, new_goal], ignore_index=True)
                    helpers.save_csv(goals_data, GOALS_FILE)
                    st.success("Savings goal saved successfully.")

    st.write("---")
    st.subheader("Saved Goals")

    _, _, goals_raw_page = get_active_data()
    goals_data = helpers.prepare_goals_data(goals_raw_page)
    if goals_data.empty:
        st.write("No savings goals added yet.")
    else:
        # Each goal as a branded card (same style as the Dashboard overview):
        # icon + name, status badge, progress bar and the key figures.
        for _, goal in goals_data.iterrows():
            progress = float(goal["progress_percentage"])
            if goal.get("is_overdue"):
                badge = '<span class="wb-goal-badge wb-goal-late">Deadline passed</span>'
            elif progress >= 100:
                badge = '<span class="wb-goal-badge wb-goal-done">Complete</span>'
            else:
                badge = '<span class="wb-goal-badge wb-goal-ok">In progress</span>'

            goal_name = html.escape(str(goal["goal_name"]))
            st.markdown(
                f'<div class="wb-goal-card">'
                f'<div><span class="wb-card-icon">🎯</span>'
                f'<span class="wb-goal-name">{goal_name}</span>{badge}</div>'
                f'<div class="wb-goal-bar">'
                f'<div class="wb-goal-fill" style="width:{min(100.0, progress):.0f}%"></div></div>'
                f'<div class="wb-goal-stats">'
                f'Saved <b>£{goal["current_amount"]:,.2f}</b> of '
                f'<b>£{goal["target_amount"]:,.2f}</b> ({progress:.1f}%) - '
                f'£{goal["remaining_amount"]:,.2f} remaining - '
                f'deadline {goal["deadline"]}</div>'
                f'</div>',
                unsafe_allow_html=True,
            )

    st.write("---")
    st.subheader("Edit or delete goals")
    if st.session_state.get("demo_mode"):
        st.caption("Editing is disabled while Demo Mode is on.")
    else:
        st.caption("Edit cells directly, or use the 🗑 / + controls to delete or add rows, then save.")

        raw_goals = helpers.load_goals()
        edited_goals = st.data_editor(
            raw_goals,
            num_rows="dynamic",
            width="stretch",
            key="goals_editor",
            column_config={
                "goal_name": st.column_config.TextColumn("Goal"),
                "target_amount": st.column_config.NumberColumn("Target (£)", min_value=0.0, step=50.0, format="£%.2f"),
                "current_amount": st.column_config.NumberColumn("Saved (£)", min_value=0.0, step=25.0, format="£%.2f"),
                "deadline": st.column_config.TextColumn("Deadline", help="YYYY-MM-DD"),
            },
        )

        if st.button("💾 Save goal changes"):
            cleaned = helpers.clean_edited_table(edited_goals, key_field="goal_name")
            helpers.save_csv(cleaned, GOALS_FILE)
            st.success("Goals updated.")
            st.rerun()


# ============================================================
# Feedback page (for user testing)
# ============================================================

elif page == "Feedback":
    st.header("Feedback")

    st.markdown(
        '<div class="wb-intro-card">'
        '<div class="wb-intro-title">Help improve WiseBudget AI</div>'
        'Share what worked, what confused you, and what you would add.'
        '</div>',
        unsafe_allow_html=True,
    )
    st.caption(
        "In the local version, feedback is saved to CSV. In the cloud demo, "
        "feedback may not persist after the app restarts."
    )

    # Single-column form keeps this page easy to fill in on a phone.
    with st.form("feedback_form"):
        would_use_app = st.radio(
            "Would you use this app?",
            ["Yes", "Maybe", "No"],
            horizontal=True,
        )
        most_useful_feature = st.selectbox(
            "Which feature did you find most useful?",
            [
                "Dashboard overview",
                "Your Top 3 Money Actions",
                "Smart Saving Opportunities",
                "AI saving plans",
                "WiseBudget AI Coach (analysis)",
                "WiseBudget AI Coach (chat)",
                "Savings Goals",
                "Adding and tracking records",
                "Something else",
            ],
        )
        preferred_spending_view = st.radio(
            "Which spending view do you prefer?",
            ["Ranked list", "Percentages", "Bar chart", "Pie chart", "Tables", "Not sure"],
        )
        what_was_confusing = st.text_area(
            "Was anything confusing?",
            placeholder="Example: I didn't understand what the savings rate meant.",
            height=80,
        )
        feature_to_add = st.text_area(
            "One feature you would add",
            placeholder="Example: monthly budgets per category.",
            height=80,
        )
        design_rating = st.slider("Design rating (1 = poor, 5 = excellent)", 1, 5, 4)
        usefulness_rating = st.slider("Usefulness rating (1 = poor, 5 = excellent)", 1, 5, 4)
        final_comments = st.text_area("Any final comments?", height=80)

        feedback_submitted = st.form_submit_button("Submit feedback")

        if feedback_submitted:
            # save_feedback returns False when the disk can't be written to
            # (some cloud hosts). The form still succeeds either way - the
            # tester's submission must never look like an error.
            stored_to_csv = helpers.save_feedback({
                "date_time": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                "would_use_app": would_use_app,
                "most_useful_feature": most_useful_feature,
                "preferred_spending_view": preferred_spending_view,
                "what_was_confusing": what_was_confusing.strip(),
                "feature_to_add": feature_to_add.strip(),
                "design_rating": design_rating,
                "usefulness_rating": usefulness_rating,
                "final_comments": final_comments.strip(),
            })
            st.success("Thank you! Your feedback has been submitted.")
            if not stored_to_csv:
                st.caption(
                    "Note: permanent storage isn't available in this cloud "
                    "demo, so this response may not persist after a restart."
                )


# ============================================================
# Investment Learning Hub page
# ============================================================

elif page == "Investment Learning Hub":
    st.header("Investment Learning Hub")

    st.markdown(
        '<div class="wb-intro-card">'
        '<div class="wb-intro-title">Learn the ideas before the products.</div>'
        'Plain-English explanations of core money concepts. Education only - '
        'no recommendations.'
        '</div>',
        unsafe_allow_html=True,
    )

    st.warning(
        "This section is for investment education only. "
        "It does not provide personal financial advice."
    )

    st.subheader("Before Investing")
    st.write(
        "Before investing, a person should usually understand their budget, "
        "control high-interest debt, and build an emergency fund."
    )

    st.subheader("Key Investing Concepts")
    # Concept cards: fixed educational copy only (no advice, no products).
    edu_cards = [
        ("⚖️", "Risk", "Investments can go up or down in value."),
        ("🧺", "Diversification",
         "Spreading money across different assets can reduce risk."),
        ("📈", "Compound growth",
         "Money can grow over time when returns are reinvested."),
        ("🛟", "Emergency fund",
         "Money kept aside for unexpected expenses before taking investment risk."),
        ("⏳", "Long-term thinking",
         "Investing is usually more suitable for long-term goals, not "
         "short-term spending needs."),
    ]
    edu_html = "".join(
        '<div class="wb-edu-card">'
        f'<span class="wb-edu-icon">{icon}</span>'
        f'<div class="wb-edu-title">{title}</div>'
        f'<div class="wb-edu-text">{text}</div>'
        '</div>'
        for icon, title, text in edu_cards
    )
    st.markdown(f'<div class="wb-edu-grid">{edu_html}</div>', unsafe_allow_html=True)

    st.subheader("Educational Note")
    st.info(
        "WiseBudget AI can help users understand how much money may be left after expenses, "
        "but it does not recommend specific stocks, funds, or investments."
    )
