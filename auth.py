from database import get_supabase_client


def sign_up(email: str, password: str):
    """Create a new Supabase user with email and password."""

    client = get_supabase_client()

    return client.auth.sign_up(
        {
            "email": email,
            "password": password,
        }
    )


def sign_in(email: str, password: str):
    """Sign in an existing Supabase user."""

    client = get_supabase_client()

    return client.auth.sign_in_with_password(
        {
            "email": email,
            "password": password,
        }
    )


def create_authenticated_client(
    access_token: str,
    refresh_token: str,
):
    """Create a Supabase client authenticated with an existing session."""

    client = get_supabase_client()

    client.auth.set_session(
        access_token,
        refresh_token,
    )

    return client


def sign_out(client) -> None:
    """Sign out the current Supabase session."""

    client.auth.sign_out()
