"""django-allauth 동작을 한채에 맞춘다."""

from allauth.account.adapter import DefaultAccountAdapter


class AccountAdapter(DefaultAccountAdapter):
    def get_email_confirmation_url(self, request, emailconfirmation):
        """인증 메일의 링크를 프론트의 인증 화면(/verify-email)으로 보낸다 (API 명세서 7.2).

        그 화면이 POST /api/auth/email/verify 로 키를 보내 인증을 마친다.
        """
        return request.build_absolute_uri(f"/verify-email?key={emailconfirmation.key}")
