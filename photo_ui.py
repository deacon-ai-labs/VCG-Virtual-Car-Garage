import hashlib


def photo_upload_token(uploaded_file) -> str:
    """Return a stable fingerprint for one uploaded file."""

    digest = hashlib.sha256(
        uploaded_file.getvalue()
    ).hexdigest()

    return (
        f"{uploaded_file.name}:"
        f"{uploaded_file.type}:"
        f"{digest}"
    )


def build_photo_uploader_css(
    widget_key: str,
    photo_url: str | None,
) -> str:
    """Build CSS that makes a Streamlit file uploader look like the photo."""

    safe_key = widget_key.replace(
        '"',
        '\\"',
    )

    if photo_url:
        safe_url = photo_url.replace(
            "'",
            "\\'",
        )

        background = (
            "linear-gradient("
            "180deg,"
            "rgba(0,0,0,0.05),"
            "rgba(0,0,0,0.28)"
            "),"
            f"url('{safe_url}')"
        )

        helper_text = (
            "Click to change photo"
        )

    else:
        background = (
            "radial-gradient("
            "circle at 50% 40%,"
            "rgba(255,107,74,0.10),"
            "transparent 38%"
            "),"
            "linear-gradient("
            "180deg,"
            "#151E29,"
            "#101821"
            ")"
        )

        helper_text = (
            "Click to add photo"
        )

    return f"""
    <style>
    .st-key-{safe_key} [data-testid="stFileUploaderDropzone"] {{
        min-height: 240px;
        border-radius: 14px;
        border: 1px solid #334456;
        background-image: {background};
        background-position: center;
        background-size: cover;
        background-repeat: no-repeat;
        cursor: pointer;
        position: relative;
        overflow: hidden;
    }}

    .st-key-{safe_key} [data-testid="stFileUploaderDropzone"]::after {{
        content: "{helper_text}";
        position: absolute;
        left: 50%;
        bottom: 14px;
        transform: translateX(-50%);
        padding: 0.45rem 0.72rem;
        border-radius: 999px;
        background: rgba(11, 17, 24, 0.82);
        border: 1px solid rgba(255, 107, 74, 0.55);
        color: #F4F7FA;
        font-size: 0.78rem;
        font-weight: 750;
        pointer-events: none;
        white-space: nowrap;
    }}

    .st-key-{safe_key} [data-testid="stFileUploaderDropzoneInstructions"] {{
        opacity: 0;
    }}

    .st-key-{safe_key} [data-testid="stFileUploaderDropzone"] button {{
        position: absolute;
        inset: 0;
        width: 100%;
        height: 100%;
        opacity: 0;
        cursor: pointer;
    }}

    .st-key-{safe_key} [data-testid="stFileUploaderDropzone"] svg {{
        opacity: 0;
    }}
    </style>
    """
