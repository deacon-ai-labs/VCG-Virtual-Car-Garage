import os

from supabase import Client, create_client


def _read_required_setting(name: str) -> str:
    """
    Read one required server setting without ever echoing its value.

    Secrets must be stored as the raw value only. Labels such as "Value:"
    and embedded/newline whitespace are rejected so malformed credentials
    cannot leak through lower-level HTTP exception messages.
    """

    value = os.environ.get(name)

    if not value:
        raise RuntimeError(
            f"{name} must be configured."
        )

    if (
        value != value.strip()
        or "\n" in value
        or "\r" in value
        or value.lower().startswith("value:")
    ):
        raise RuntimeError(
            f"{name} is malformed. Re-save it as the raw value only, "
            "with no 'Value:' label, spaces, or line breaks."
        )

    return value


def get_private_knowledge_credentials() -> tuple[str, str]:
    """Return validated Supabase URL and server-only secret API key."""

    supabase_url = _read_required_setting(
        "SUPABASE_URL"
    )
    secret_key = _read_required_setting(
        "SUPABASE_SECRET_KEY"
    )

    return (
        supabase_url,
        secret_key,
    )


def get_knowledge_admin_client() -> Client:
    """
    Return the server-only Supabase client used for VCG knowledge.

    Supabase secret API keys bypass RLS, so they must only exist in trusted
    server/admin environments and must never be committed to Git.
    """

    (
        supabase_url,
        secret_key,
    ) = get_private_knowledge_credentials()

    return create_client(
        supabase_url,
        secret_key,
    )
