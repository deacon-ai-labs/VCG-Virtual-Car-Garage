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


def user_auth_error_message(
    error: Exception,
    action: str = "sign in",
) -> str:
    """Return a safe, useful message for authentication failures."""

    message = str(error).lower()

    configuration_markers = (
        "unregistered api key",
        "unauthorized_unregistered_api_key",
        "invalid api key",
        "apikey",
    )

    if any(
        marker in message
        for marker in configuration_markers
    ):
        return (
            "VCG authentication is temporarily misconfigured. "
            "The Supabase API key used by this environment is not valid."
        )

    credential_markers = (
        "invalid login credentials",
        "email not confirmed",
    )

    if any(
        marker in message
        for marker in credential_markers
    ):
        return (
            "Sign in failed. Check your email and password and try again."
        )

    return (
        f"VCG could not {action}. "
        "The authentication service returned an unexpected error."
    )



def signup_password_error(
    password: str,
) -> str | None:
    """Return a user-facing VCG password-policy error, or None."""

    if len(
        password
    ) < 12:
        return (
            "Use at least 12 characters for your password."
        )

    if not any(
        character.isalpha()
        for character in password
    ):
        return (
            "Include at least one letter in your password."
        )

    if not any(
        character.isdigit()
        for character in password
    ):
        return (
            "Include at least one number in your password."
        )

    return None
