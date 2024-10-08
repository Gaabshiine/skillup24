from django.contrib.auth.tokens import PasswordResetTokenGenerator
import six

# Token Generator Class
class TokenGenerator(PasswordResetTokenGenerator):
    def _make_hash_value(self, user, timestamp):
        return (
            six.text_type(user['id']) + six.text_type(timestamp) + six.text_type(user['password'])
        )

account_activation_token = TokenGenerator()