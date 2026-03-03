from nala.domain.hr.tools.register import HRToolRegister


def register_api_domain_initializers() -> None:
    """Entry point for the API layer to register all its domain initialization functions.

    This function is called only once at the start of the application's lifecycle.
    It hooks domain-specific dependencies and tools into the global framework registries.
    """
    HRToolRegister.register_all()
