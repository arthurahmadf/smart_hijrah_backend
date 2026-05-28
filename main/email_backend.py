from django.core.mail.backends.smtp import EmailBackend
import ssl

class NoSSLVerifyEmailBackend(EmailBackend):
    def open(self):
        if self.connection:
            return False
        try:
            self.connection = self.connection_class(
                self.host, self.port,
                timeout=self.timeout,
            )
            # Disable certificate verification
            self.connection.starttls(context=ssl._create_unverified_context())
            self.connection.ehlo()
            if self.username and self.password:
                self.connection.login(self.username, self.password)
            return True
        except Exception:
            if not self.fail_silently:
                raise