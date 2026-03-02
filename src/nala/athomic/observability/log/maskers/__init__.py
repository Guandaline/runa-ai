from nala.athomic.observability.log.maskers.cpf_masker import CPFMasker
from nala.athomic.observability.log.maskers.email_masker import EmailMasker
from nala.athomic.observability.log.maskers.phone_masker import PhoneMasker
from nala.athomic.observability.log.registry import register_masker

# Register all maskers
register_masker(CPFMasker)
register_masker(EmailMasker)
register_masker(PhoneMasker)
