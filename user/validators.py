from django.contrib.auth import get_user_model
from django.core.exceptions import ValidationError


class RegisteredEmailValidator:
    user_model = get_user_model()
    code = 'invalid'

    def __call__(self, email):
        try:
            user = self.user_model.objects.get(email=email)
        except self.user_model.DoesNotExist:
            raise ValidationError('가입되지 않은 이메일입니다.', code=self.code)
        else:
            if user.is_active:
                raise ValidationError('이미 인증되어 있습니다.', code=self.code)

        return