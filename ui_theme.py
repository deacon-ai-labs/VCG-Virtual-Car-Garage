import base64
from pathlib import Path

import streamlit as st


VCG_ORANGE = "#FF6B4A"
VCG_ORANGE_HOVER = "#FF7B5C"
VCG_BG = "#0B1118"
VCG_PANEL = "#111A24"
VCG_PANEL_ALT = "#17212D"
VCG_BORDER = "#283646"
VCG_TEXT = "#F4F7FA"
VCG_MUTED = "#9AA8B7"


def image_data_uri(
    path: str | Path,
) -> str:
    """Return a local PNG/JPG asset as a data URI."""

    image_path = Path(path)
    suffix = image_path.suffix.lower()

    if suffix in {".jpg", ".jpeg"}:
        mime = "image/jpeg"
    elif suffix == ".webp":
        mime = "image/webp"
    else:
        mime = "image/png"

    encoded = base64.b64encode(
        image_path.read_bytes()
    ).decode("ascii")

    return (
        f"data:{mime};base64,{encoded}"
    )


def apply_global_theme() -> None:
    """Apply the shared Virtual Car Garage visual system."""

    st.markdown(
        f"""
        <style>
        :root {{
            --vcg-orange: {VCG_ORANGE};
            --vcg-orange-hover: {VCG_ORANGE_HOVER};
            --vcg-bg: {VCG_BG};
            --vcg-panel: {VCG_PANEL};
            --vcg-panel-alt: {VCG_PANEL_ALT};
            --vcg-border: {VCG_BORDER};
            --vcg-text: {VCG_TEXT};
            --vcg-muted: {VCG_MUTED};
        }}

        html, body, [class*="css"] {{
            color: var(--vcg-text);
        }}

        .stApp {{
            background:
                radial-gradient(
                    circle at 20% 0%,
                    rgba(255, 107, 74, 0.05),
                    transparent 28%
                ),
                linear-gradient(
                    180deg,
                    #0B1118 0%,
                    #0A1016 100%
                );
        }}

        [data-testid="stHeader"] {{
            background: rgba(11, 17, 24, 0.80);
            border-bottom: 1px solid rgba(255,255,255,0.04);
        }}

        .block-container {{
            max-width: 1800px;
            padding-top: 1.5rem;
            padding-bottom: 2rem;
        }}

        [data-testid="stSidebar"] {{
            background:
                linear-gradient(
                    180deg,
                    #151D28 0%,
                    #111821 100%
                );
            border-right: 1px solid var(--vcg-border);
        }}

        h1, h2, h3 {{
            color: var(--vcg-text) !important;
            letter-spacing: -0.02em;
        }}

        p, label, .stCaption {{
            color: var(--vcg-muted);
        }}

        div[data-testid="stForm"],
        div[data-testid="stExpander"] {{
            border: 1px solid var(--vcg-border);
            border-radius: 14px;
            background: rgba(17, 26, 36, 0.86);
        }}

        div[data-testid="stTextInput"] input,
        div[data-testid="stTextArea"] textarea,
        div[data-testid="stNumberInput"] input {{
            background: #111A24 !important;
            color: var(--vcg-text) !important;
            border: 1px solid #314153 !important;
            border-radius: 10px !important;
        }}

        div[data-testid="stTextInput"] input:focus,
        div[data-testid="stTextArea"] textarea:focus,
        div[data-testid="stNumberInput"] input:focus {{
            border-color: var(--vcg-orange) !important;
            box-shadow: 0 0 0 1px var(--vcg-orange) !important;
        }}

        .stButton > button,
        .stFormSubmitButton > button {{
            border-radius: 10px;
            border: 1px solid #344356;
            background: #17212D;
            color: var(--vcg-text);
            font-weight: 650;
            transition: 0.15s ease;
        }}

        .stButton > button:hover,
        .stFormSubmitButton > button:hover {{
            border-color: var(--vcg-orange);
            color: white;
        }}

        .stButton > button[kind="primary"],
        .stFormSubmitButton > button[kind="primary"] {{
            border: none;
            color: #0B1118;
            background:
                linear-gradient(
                    90deg,
                    var(--vcg-orange),
                    #FF8467
                );
            font-weight: 800;
        }}

        .stButton > button[kind="primary"]:hover,
        .stFormSubmitButton > button[kind="primary"]:hover {{
            background:
                linear-gradient(
                    90deg,
                    var(--vcg-orange-hover),
                    #FF9278
                );
            color: #0B1118;
        }}

        button[data-baseweb="tab"] {{
            color: #B7C2CE;
            font-weight: 700;
        }}

        button[data-baseweb="tab"][aria-selected="true"] {{
            color: white;
        }}

        div[data-baseweb="tab-highlight"] {{
            background-color: var(--vcg-orange) !important;
        }}

        div[data-testid="stChatMessage"] {{
            background: #121C27;
            border: 1px solid #263646;
            border-radius: 14px;
            padding: 0.7rem 0.9rem;
            margin-bottom: 0.7rem;
        }}

        [data-testid="stChatInput"] {{
            background: #0E1620;
            border: 1px solid #334456;
            border-radius: 13px;
        }}

        [data-testid="stChatInput"]:focus-within {{
            border-color: var(--vcg-orange);
        }}

        .vcg-wordmark {{
            display: flex;
            align-items: center;
            gap: 0.65rem;
            margin-bottom: 0.45rem;
        }}

        .vcg-mark {{
            width: 42px;
            height: 3px;
            border-radius: 999px;
            background: var(--vcg-orange);
            box-shadow:
                11px -6px 0 -1px var(--vcg-orange),
                22px -2px 0 -1px var(--vcg-orange);
        }}

        .vcg-wordmark-text {{
            font-size: 1.45rem;
            font-weight: 850;
            letter-spacing: 0.02em;
            color: #F3F6F9;
        }}

        .vcg-wordmark-text span {{
            color: var(--vcg-orange);
        }}

        .vcg-auth-shell {{
            border: 1px solid var(--vcg-border);
            background:
                linear-gradient(
                    180deg,
                    rgba(20, 30, 41, 0.98),
                    rgba(15, 23, 32, 0.98)
                );
            border-radius: 18px;
            padding: 1.55rem 1.5rem 1.35rem 1.5rem;
            box-shadow:
                0 22px 60px rgba(0,0,0,0.28);
            margin-top: 0.25rem;
        }}

        .vcg-auth-kicker {{
            color: var(--vcg-muted);
            font-size: 1.02rem;
            margin-bottom: 0.85rem;
        }}

        .vcg-auth-note {{
            margin-top: 1rem;
            padding: 0.85rem 1rem;
            border-radius: 12px;
            border: 1px solid #2A394A;
            background: #111A24;
            color: #9EABB9;
            font-size: 0.91rem;
        }}

        .vcg-login-hero {{
            overflow: hidden;
            border-radius: 18px;
            border: 1px solid #223040;
            background: #0D141D;
            box-shadow:
                0 26px 70px rgba(0,0,0,0.30);
            aspect-ratio: 1095 / 941;
            min-height: 0;
        }}

        .vcg-login-hero img {{
            display: block;
            width: 100%;
            height: 100%;
            min-height: 0;
            object-fit: contain;
            object-position: center;
            background: #0D141D;
        }}


        .vcg-top-divider {{
            height: 1px;
            background: linear-gradient(
                90deg,
                rgba(255, 107, 74, 0.42),
                rgba(40, 54, 70, 0.95),
                transparent
            );
            margin: 0.35rem 0 1rem 0;
        }}

        .vcg-section-heading {{
            display: flex;
            align-items: center;
            justify-content: space-between;
            border: 1px solid var(--vcg-border);
            background:
                linear-gradient(
                    180deg,
                    rgba(20, 30, 41, 0.98),
                    rgba(15, 23, 32, 0.98)
                );
            border-radius: 14px;
            padding: 0.95rem 1rem;
            margin-bottom: 0.45rem;
        }}

        .vcg-section-kicker {{
            color: var(--vcg-orange);
            font-size: 0.72rem;
            font-weight: 850;
            letter-spacing: 0.12em;
            text-transform: uppercase;
            margin-bottom: 0.25rem;
        }}

        .vcg-section-title {{
            color: var(--vcg-text);
            font-size: 1.42rem;
            font-weight: 850;
            letter-spacing: -0.02em;
        }}

        .vcg-photo-placeholder {{
            width: 100%;
            border-radius: 12px;
            border: 1px dashed #334456;
            background:
                radial-gradient(
                    circle at 50% 40%,
                    rgba(255, 107, 74, 0.09),
                    transparent 38%
                ),
                linear-gradient(
                    180deg,
                    #151E29,
                    #101821
                );
            color: #7E8B99;
            display: flex;
            flex-direction: column;
            align-items: center;
            justify-content: center;
            gap: 0.35rem;
            overflow: hidden;
        }}

        .vcg-photo-placeholder span {{
            font-size: 2rem;
            opacity: 0.78;
        }}

        .vcg-photo-placeholder small {{
            font-size: 0.78rem;
            color: #7E8B99;
        }}

        .vcg-photo-small {{
            min-height: 118px;
            margin-bottom: 0.55rem;
        }}

        .vcg-photo-large {{
            min-height: 235px;
            margin-bottom: 0.85rem;
        }}

        [data-testid="stImage"] img {{
            border-radius: 12px;
        }}

        .vcg-maintenance-shell {{
            border: 1px solid var(--vcg-border);
            background: #111A24;
            border-radius: 14px;
            padding: 1rem;
            margin-top: 1rem;
        }}

        .vcg-maintenance-title {{
            color: var(--vcg-text);
            font-weight: 800;
            font-size: 1rem;
            margin-bottom: 0.55rem;
        }}

        .vcg-maintenance-empty {{
            color: var(--vcg-muted);
            font-size: 0.88rem;
            line-height: 1.45;
        }}

        div[data-testid="stMetric"] {{
            border-color: var(--vcg-border) !important;
            background: rgba(17, 26, 36, 0.72);
            border-radius: 12px;
        }}

        div[data-testid="stMetric"] label {{
            color: var(--vcg-muted) !important;
        }}

        div[data-testid="stMetricValue"] {{
            color: var(--vcg-text) !important;
            font-size: 1.05rem;
        }}

        [data-testid="stHorizontalBlock"] {{
            align-items: flex-start;
        }}

        @media (max-width: 900px) {{
            .vcg-login-hero {{
                aspect-ratio: 1095 / 941;
                min-height: 0;
            }}

            .vcg-login-hero img {{
                min-height: 0;
                object-fit: contain;
            }}
        }}
        </style>
        """,
        unsafe_allow_html=True,
    )


def render_wordmark() -> None:
    """Render the VCG wordmark."""

    st.markdown(
        """
        <div class="vcg-wordmark">
            <div class="vcg-mark"></div>
            <div class="vcg-wordmark-text">
                VIRTUAL <span>CAR GARAGE</span>
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )

def dashboard_shell_css() -> str:
    """Return CSS for the fixed dashboard shell and independent panel scrolling."""

    return """
        <style>
        .vcg-rail-kicker,
        .vcg-rail-section {
            color: var(--vcg-orange);
            font-size: 0.68rem;
            font-weight: 850;
            letter-spacing: 0.14em;
            text-transform: uppercase;
        }

        .vcg-rail-title {
            color: var(--vcg-text);
            font-size: 1.18rem;
            font-weight: 850;
            margin-top: 0.12rem;
        }

        .vcg-rail-section {
            margin-top: 1.15rem;
            margin-bottom: 0.45rem;
            color: #7F8FA1;
        }

        .vcg-spotlight {
            border: 1px solid var(--vcg-border);
            background:
                radial-gradient(
                    circle at 95% 0%,
                    rgba(255, 107, 74, 0.10),
                    transparent 35%
                ),
                linear-gradient(
                    135deg,
                    rgba(21, 31, 43, 0.98),
                    rgba(13, 21, 30, 0.98)
                );
            border-radius: 18px;
            padding: 1.25rem 1.35rem;
            min-height: 210px;
            display: flex;
            flex-direction: column;
            justify-content: center;
        }

        .vcg-spotlight-profile {
            color: var(--vcg-orange);
            font-size: 0.82rem;
            font-weight: 750;
            margin-bottom: 0.18rem;
        }

        .vcg-spotlight-title {
            color: var(--vcg-text);
            font-size: clamp(1.55rem, 2vw, 2.25rem);
            font-weight: 900;
            letter-spacing: -0.035em;
            line-height: 1.05;
        }

        .vcg-spotlight-subtitle {
            color: #AAB6C3;
            font-size: 0.93rem;
            margin-top: 0.45rem;
        }

        .vcg-status-grid {
            display: grid;
            grid-template-columns: repeat(3, minmax(0, 1fr));
            gap: 0.65rem;
            margin-top: 1rem;
        }

        .vcg-status-card {
            border: 1px solid #2B3A4B;
            border-radius: 12px;
            background: rgba(10, 17, 24, 0.52);
            padding: 0.7rem 0.8rem;
            min-width: 0;
        }

        .vcg-status-card span {
            display: block;
            color: #778799;
            font-size: 0.62rem;
            font-weight: 850;
            letter-spacing: 0.10em;
        }

        .vcg-status-card strong {
            display: block;
            color: #F4F7FA;
            font-size: 0.95rem;
            margin-top: 0.2rem;
            white-space: nowrap;
            overflow: hidden;
            text-overflow: ellipsis;
        }

        .vcg-status-card small {
            display: block;
            color: #8F9DAA;
            font-size: 0.70rem;
            margin-top: 0.08rem;
        }

        .vcg-photo-spotlight {
            min-height: 210px;
            margin-bottom: 0;
        }

        .st-key-vcg_spotlight_photo [data-testid="stImage"] img {
            min-height: 210px;
            max-height: 245px;
            width: 100%;
            object-fit: cover;
            object-position: center;
            border: 1px solid #283646;
            box-shadow: 0 18px 40px rgba(0,0,0,0.24);
        }

        .vcg-workspace-divider {
            height: 1px;
            margin: 0.85rem 0;
            background:
                linear-gradient(
                    90deg,
                    rgba(255,107,74,0.35),
                    rgba(40,54,70,0.8),
                    transparent
                );
        }

        .vcg-live-pill {
            border: 1px solid rgba(255, 107, 74, 0.34);
            background: rgba(255, 107, 74, 0.08);
            color: #FF9A82;
            border-radius: 999px;
            padding: 0.32rem 0.55rem;
            font-size: 0.61rem;
            font-weight: 850;
            letter-spacing: 0.08em;
            white-space: nowrap;
        }

        .vcg-ai-empty {
            border: 1px dashed #334456;
            border-radius: 14px;
            background: rgba(17, 26, 36, 0.52);
            padding: 1.05rem;
            margin-top: 0.45rem;
        }

        .vcg-ai-empty strong,
        .vcg-ai-empty span {
            display: block;
        }

        .vcg-ai-empty strong {
            color: #F4F7FA;
            font-size: 0.98rem;
        }

        .vcg-ai-empty span {
            color: #8E9CAB;
            font-size: 0.86rem;
            line-height: 1.45;
            margin-top: 0.25rem;
        }

        .vcg-mini-divider {
            height: 1px;
            background: #253342;
            margin: 0.65rem 0;
        }

        .vcg-empty-garage {
            border: 1px solid var(--vcg-border);
            border-radius: 18px;
            padding: 2rem;
            background: #111A24;
        }

        .vcg-empty-garage p {
            max-width: 620px;
        }

        [data-testid="stAppViewContainer"] {
            overflow-y: hidden;
            overflow-x: hidden;
        }

        /*
        Do not clip the block container itself: the chat composer is rendered
        after the scroll pane and must remain visible.
        */
        .block-container {
            height: auto;
            max-height: none;
            overflow: visible;
            padding-bottom: 0.65rem;
        }

        .st-key-vcg_garage_scroll,
        .st-key-vcg_insights_scroll {
            height: calc(100vh - 150px);
            max-height: calc(100vh - 150px);
            overflow-y: auto;
            overflow-x: hidden;
            padding-right: 0.35rem;
            scrollbar-width: thin;
            scrollbar-color: #455568 transparent;
        }

        /*
        Reserve explicit vertical space for the Garage AI header, caption and
        composer. This keeps the prompt visible at normal browser zoom.
        */
        .st-key-vcg_workshop_scroll {
            height: calc(100vh - 405px);
            max-height: calc(100vh - 405px);
            min-height: 320px;
            overflow-y: auto;
            overflow-x: hidden;
            padding-right: 0.55rem;
            scrollbar-width: thin;
            scrollbar-color: #455568 transparent;
        }

        .st-key-vcg_chat_scroll {
            height: calc(100vh - 515px);
            max-height: calc(100vh - 515px);
            min-height: 220px;
            overflow-y: auto;
            overflow-x: hidden;
            padding-right: 0.55rem;
            margin-bottom: 0.55rem;
            scrollbar-width: thin;
            scrollbar-color: #455568 transparent;
        }

        .st-key-vcg_garage_scroll::-webkit-scrollbar,
        .st-key-vcg_insights_scroll::-webkit-scrollbar,
        .st-key-vcg_workshop_scroll::-webkit-scrollbar,
        .st-key-vcg_chat_scroll::-webkit-scrollbar {
            width: 7px;
        }

        .st-key-vcg_garage_scroll::-webkit-scrollbar-thumb,
        .st-key-vcg_insights_scroll::-webkit-scrollbar-thumb,
        .st-key-vcg_workshop_scroll::-webkit-scrollbar-thumb,
        .st-key-vcg_chat_scroll::-webkit-scrollbar-thumb {
            background: #455568;
            border-radius: 999px;
        }

        .st-key-vcg_garage_scroll::-webkit-scrollbar-track,
        .st-key-vcg_insights_scroll::-webkit-scrollbar-track,
        .st-key-vcg_workshop_scroll::-webkit-scrollbar-track,
        .st-key-vcg_chat_scroll::-webkit-scrollbar-track {
            background: transparent;
        }

        [data-testid="stChatInput"] {
            position: relative;
            z-index: 4;
            margin-top: 0.2rem;
            box-shadow: 0 -10px 24px rgba(11, 17, 24, 0.75);
        }

        @media (max-height: 760px) {
            .st-key-vcg_garage_scroll,
            .st-key-vcg_insights_scroll {
                height: calc(100vh - 135px);
                max-height: calc(100vh - 135px);
            }

            .st-key-vcg_workshop_scroll {
                height: calc(100vh - 370px);
                max-height: calc(100vh - 370px);
                min-height: 260px;
            }

            .st-key-vcg_chat_scroll {
                height: calc(100vh - 485px);
                max-height: calc(100vh - 485px);
                min-height: 180px;
            }
        }

        /*
        Mobile browser fallback:
        - restore normal document scrolling
        - let Streamlit columns stack vertically
        - remove fixed side-panel heights
        - keep chat history usable without trying to imitate the native app
        */
        @media (max-width: 900px) {
            [data-testid="stAppViewContainer"] {
                overflow-y: auto;
                overflow-x: hidden;
            }

            .block-container {
                height: auto;
                max-height: none;
                overflow: visible;
                padding-left: 0.75rem;
                padding-right: 0.75rem;
                padding-bottom: 1.25rem;
            }

            [data-testid="stHorizontalBlock"] {
                flex-wrap: wrap !important;
                gap: 0.75rem !important;
            }

            [data-testid="column"] {
                flex: 1 1 100% !important;
                width: 100% !important;
                min-width: 100% !important;
            }

            .st-key-vcg_garage_scroll,
            .st-key-vcg_insights_scroll,
            .st-key-vcg_workshop_scroll {
                height: auto;
                max-height: none;
                overflow: visible;
                padding-right: 0;
            }

            .st-key-vcg_chat_scroll {
                height: auto;
                max-height: 60vh;
                min-height: 260px;
                overflow-y: auto;
                overflow-x: hidden;
                padding-right: 0.25rem;
                margin-bottom: 0.5rem;
            }

            [data-testid="stChatInput"] {
                position: relative;
                bottom: auto;
                margin-top: 0.25rem;
                box-shadow: none;
            }

            .vcg-status-grid {
                grid-template-columns: 1fr;
            }

            .vcg-photo-large {
                min-height: 210px;
            }

            .vcg-login-hero,
            .vcg-login-hero img {
                min-height: 0;
            }
        }
        </style>
    """


def apply_dashboard_shell() -> None:
    """Apply the signed-in dashboard scrolling shell."""

    st.markdown(
        dashboard_shell_css(),
        unsafe_allow_html=True,
    )
